from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from academics.models import TeacherAssignment, Enrollment
from curriculum.models import SchemeWeek, SchemeOfWork
from .models import (
    Course, Lesson, CourseEnrollment, LessonProgress, Topic,
    Quiz, QuizQuestion, QuizAttempt, LessonComment, LearningMaterial,
    Post, PostComment, Assignment, Submission,
)
from .serializers import (
    CourseSerializer, LessonSerializer, LessonProgressSerializer,
    TopicSerializer, QuizSerializer, QuizQuestionSerializer,
    QuizAttemptSerializer, LessonCommentSerializer, LearningMaterialSerializer,
    PostSerializer, PostCommentSerializer, CourseAssignmentSerializer, SubmissionSerializer,
)


class CoursePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or obj.teacher == request.user


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, CoursePermission]

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.filter(school=user.school)

        if user.role == 'TEACHER':
            my_areas = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('learning_area', flat=True)
            return qs.filter(Q(author=user) | Q(teacher=user) | Q(status='published', learning_area__in=my_areas)).distinct()

        elif user.role in ['STUDENT', 'PARENT']:
            enrollments = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            return qs.filter(id__in=enrollments, status='published')

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(school=user.school, author=user, teacher=user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        course = self.get_object()
        school = request.user.school
        settings = school.settings

        if settings.requires_course_review and course.status != 'submitted_for_review':
            course.status = 'submitted_for_review'
            course.save()
            return Response({"detail": "Course submitted for review."})

        course.status = 'published'
        course.save()

        if course.delivery_mode in ['teacher_led', 'blended']:
            if course.stream:
                learners = Enrollment.objects.filter(stream=course.stream, is_active=True).values_list('student', flat=True)
            else:
                streams = TeacherAssignment.objects.filter(teacher=request.user, learning_area=course.learning_area).values_list('stream', flat=True)
                learners = Enrollment.objects.filter(stream__in=streams, is_active=True).values_list('student', flat=True)

            enrollments = [CourseEnrollment(course=course, learner_id=l_id, school=school) for l_id in learners]
            CourseEnrollment.objects.bulk_create(enrollments, ignore_conflicts=True)

        return Response({"detail": "Course published and learners enrolled."})

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        learner_id = request.data.get('learner_id') or request.data.get('student_id')
        if not learner_id:
            return Response({"detail": "learner_id is required."}, status=400)
        obj, created = CourseEnrollment.objects.get_or_create(
            course=course, learner_id=learner_id, school=request.user.school)
        return Response({
            "detail": "Learner enrolled." if created else "Learner already enrolled.",
            "enrollment": {"id": obj.id, "learner": obj.learner_id, "course": obj.course_id},
        })

    @action(detail=True, methods=['post'])
    def unenroll(self, request, pk=None):
        course = self.get_object()
        learner_id = request.data.get('learner_id') or request.data.get('student_id')
        if not learner_id:
            return Response({"detail": "learner_id is required."}, status=400)
        deleted, _ = CourseEnrollment.objects.filter(course=course, learner_id=learner_id).delete()
        return Response({"detail": "Learner unenrolled." if deleted else "Learner was not enrolled."})

    @action(detail=True, methods=['post'])
    def enroll_by_grade(self, request, pk=None):
        course = self.get_object()
        grade_id = request.data.get('grade_id')
        if not grade_id:
            return Response({"detail": "grade_id is required."}, status=400)
        learner_ids = Enrollment.objects.filter(
            stream__grade_id=grade_id, school=course.school, is_active=True
        ).values_list('student', flat=True).distinct()
        count = 0
        for lid in learner_ids:
            _, created = CourseEnrollment.objects.get_or_create(
                course=course, learner_id=lid, school=course.school)
            if created:
                count += 1
        return Response({"detail": f"Enrolled {count} learner(s) from grade {grade_id}."})

    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        course = self.get_object()
        rows = CourseEnrollment.objects.filter(course=course).select_related('learner')
        data = [{
            'id': e.id,
            'learner_id': e.learner_id,
            'learner_name': f"{e.learner.first_name} {e.learner.last_name}".strip() or e.learner.email,
            'enrolled_at': e.enrolled_at,
        } for e in rows]
        return Response(data)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        original = self.get_object()
        if original.status != 'published':
            return Response({"detail": "Can only clone published courses."}, status=400)

        clone = Course.objects.create(
            school=original.school,
            learning_area=original.learning_area,
            author=request.user,
            teacher=request.user,
            grade=original.grade,
            stream=original.stream,
            term=original.term,
            year=original.year,
            title=f"Copy of {original.title}",
            description=original.description,
            delivery_mode=original.delivery_mode,
            cloned_from=original,
            status='draft'
        )
        for lesson in original.lessons.all():
            Lesson.objects.create(course=clone, sub_strand=lesson.sub_strand, title=lesson.title, content=lesson.content, order=lesson.order, school=original.school)

        return Response(CourseSerializer(clone).data)

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        course = self.get_object()
        qs = Topic.objects.filter(course=course, school=request.user.school)
        if request.user.role in ['STUDENT', 'PARENT']:
            qs = qs.filter(is_published=True)
        serializer = TopicSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        course = self.get_object()
        qs = Assignment.objects.filter(course=course, school=request.user.school)
        if request.user.role in ['STUDENT', 'PARENT']:
            qs = qs.filter(course__enrollments__learner=request.user)
        serializer = CourseAssignmentSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        course = self.get_object()
        qs = Post.objects.filter(course=course, school=request.user.school)
        if request.user.role in ['STUDENT', 'PARENT']:
            qs = qs.filter(course__enrollments__learner=request.user)
        serializer = PostSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_topics_from_scheme(self, request, pk=None):
        course = self.get_object()
        scheme_id = request.data.get('scheme_id')
        if scheme_id:
            try:
                scheme = SchemeOfWork.objects.get(id=scheme_id, school=course.school)
                scheme_weeks = SchemeWeek.objects.filter(scheme=scheme)
            except SchemeOfWork.DoesNotExist:
                return Response({"detail": "Scheme not found."}, status=404)
        else:
            scheme_weeks = SchemeWeek.objects.filter(scheme__learning_area=course.learning_area, scheme__stream=course.stream, scheme__term=course.term, scheme__school=course.school)
        created = []
        for sw in scheme_weeks:
            topic, _ = Topic.objects.get_or_create(
                course=course,
                scheme_entry=sw,
                defaults={
                    'title': sw.sub_strand.name,
                    'week': sw.week_number,
                    'order': sw.week_number,
                    'school': course.school,
                    'learning_area': course.learning_area,
                    'learning_outcomes': sw.specific_learning_outcomes,
                }
            )
            created.append(topic.id)
        return Response({"detail": f"Generated {len(created)} topics.", "topic_ids": created})


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Topic.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            return (qs.filter(course__author=user) | qs.filter(course__teacher=user) | qs.filter(learning_area__in=user.subject_specializations.all())).distinct()
        if user.role in ['STUDENT', 'PARENT']:
            enrolled = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            return qs.filter(course__id__in=enrolled, is_published=True)
        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        topic = self.get_object()
        topic.is_published = True
        topic.save()
        return Response({"detail": "Topic published."})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        topic = self.get_object()
        topic.is_published = False
        topic.save()
        return Response({"detail": "Topic unpublished."})


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.filter(school=user.school)
        if user.role in ['STUDENT', 'PARENT']:
            enrolled = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            qs = qs.filter(course__id__in=enrolled, course__status='published')
            now = timezone.now()
            qs = qs.filter(is_published=True).filter(
                Q(publish_at__isnull=True) | Q(publish_at__lte=now))
        return qs

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if course.author != self.request.user and course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored or teach.")
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.course.author != self.request.user and serializer.instance.course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored or teach.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.course.author != self.request.user and instance.course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored or teach.")
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        lesson = self.get_object()
        lesson.is_published = True
        lesson.save()
        return Response({"detail": "Lesson published. Topic is now active."})

    @action(detail=True, methods=['get'])
    def required_items(self, request, pk=None):
        from requirements.models import RequiredItem
        lesson = self.get_object()
        course = lesson.course
        grade = course.grade
        items = RequiredItem.objects.filter(school=course.school, class_level=grade, is_published=True)
        data = [{'id': i.id, 'name': i.name, 'description': i.description,
                 'is_mandatory': i.is_mandatory, 'preferred_source': i.preferred_source}
                for i in items]
        return Response(data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        lesson = self.get_object()
        lesson.is_published = False
        lesson.save()
        return Response({"detail": "Lesson unpublished."})


class QuizViewSet(viewsets.ModelViewSet):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['STUDENT', 'PARENT']:
            return Quiz.objects.filter(
                lesson__course__enrollments__learner=user,
                lesson__is_published=True,
                lesson__course__status='published')
        return Quiz.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def attempt(self, request, pk=None):
        quiz = self.get_object()
        answers = request.data.get('answers', {})
        questions = quiz.questions.all()
        total = questions.count()
        score = 0
        for q in questions:
            if str(answers.get(str(q.id))).upper() == q.correct:
                score += 1
        attempt = QuizAttempt.objects.create(
            quiz=quiz, learner=request.user, score=score, total=total,
            school=request.user.school)
        return Response(QuizAttemptSerializer(attempt).data)


class LessonCommentViewSet(viewsets.ModelViewSet):
    serializer_class = LessonCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LessonComment.objects.filter(school=self.request.user.school)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}


class LessonProgressViewSet(viewsets.ModelViewSet):
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LessonProgress.objects.filter(school=self.request.user.school)

    @action(detail=False, methods=['post'])
    def mark_delivered(self, request):
        lesson_id = request.data.get('lesson_id')
        stream_id = request.data.get('stream_id')

        learners = Enrollment.objects.filter(stream_id=stream_id, is_active=True).values_list('student_id', flat=True)
        for l_id in learners:
            LessonProgress.objects.update_or_create(
                lesson_id=lesson_id, learner_id=l_id,
                defaults={
                    'is_completed': True,
                    'completed_at': timezone.now(),
                    'marked_by': request.user,
                    'school': request.user.school,
                }
            )
        return Response({"detail": f"Lesson marked delivered for {len(learners)} learners."})

    @action(detail=False, methods=['post'])
    def self_paced_complete(self, request):
        lesson_id = request.data.get('lesson_id')
        progress, _ = LessonProgress.objects.update_or_create(
            lesson_id=lesson_id, learner=request.user,
            defaults={'is_completed': True, 'completed_at': timezone.now(), 'school': request.user.school}
        )
        return Response(self.get_serializer(progress).data)


class LearningMaterialViewSet(viewsets.ModelViewSet):
    serializer_class = LearningMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LearningMaterial.objects.filter(school=user.school)
        if user.role in ['STUDENT', 'PARENT']:
            enrolled = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            qs = qs.filter(lesson__course__id__in=enrolled, lesson__course__status='published',
                           lesson__is_published=True)
        return qs

    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        if lesson.course.author != self.request.user and lesson.course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add materials to lessons in courses you authored or teach.")
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.lesson.course.author != self.request.user and serializer.instance.lesson.course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit materials in courses you authored or teach.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.lesson.course.author != self.request.user and instance.lesson.course.teacher != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete materials in courses you authored or teach.")
        instance.delete()


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['topic', 'course', 'post_type']

    def get_queryset(self):
        user = self.request.user
        qs = Post.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            return qs.filter(teacher=user)
        if user.role in ['STUDENT', 'PARENT']:
            enrolled = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            return qs.filter(course__id__in=enrolled)
        return qs

    def perform_create(self, serializer):
        topic = serializer.validated_data.get('topic')
        if topic:
            course = topic.course
            if course.author != self.request.user and course.teacher != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only add posts to topics in courses you authored or teach.")
            serializer.save(teacher=self.request.user, school=self.request.user.school, course=topic.course)
        else:
            serializer.save(teacher=self.request.user, school=self.request.user.school)


class PostCommentViewSet(viewsets.ModelViewSet):
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['post']

    def get_queryset(self):
        return PostComment.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = CourseAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['topic', 'course']

    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            return qs.filter(teacher=user)
        if user.role in ['STUDENT', 'PARENT']:
            enrolled = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            return qs.filter(course__id__in=enrolled)
        return qs

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Submission.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            return qs.filter(assignment__teacher=user)
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        submission = self.get_object()
        if submission.assignment.teacher != request.user:
            return Response({"detail": "Only the assignment teacher can grade."}, status=403)
        score = request.data.get('score')
        if score is not None:
            try:
                submission.score = int(score)
            except (ValueError, TypeError):
                return Response({"detail": "Score must be an integer."}, status=400)
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        return Response(SubmissionSerializer(submission).data)
