from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from academics.models import TeacherAssignment, Enrollment
from .models import (
    Course, Lesson, CourseEnrollment, LessonProgress, Topic,
    Quiz, QuizQuestion, QuizAttempt, LessonComment,
)
from .serializers import (
    CourseSerializer, LessonSerializer, LessonProgressSerializer,
    TopicSerializer, QuizSerializer, QuizQuestionSerializer,
    QuizAttemptSerializer, LessonCommentSerializer, LearningMaterialSerializer,
)


class CoursePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, CoursePermission]

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.filter(school=user.school)

        if user.role == 'TEACHER':
            my_areas = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('learning_area', flat=True)
            return qs.filter(Q(author=user) | Q(status='published', learning_area__in=my_areas)).distinct()

        elif user.role in ['STUDENT', 'PARENT']:
            enrollments = CourseEnrollment.objects.filter(learner=user).values_list('course_id', flat=True)
            return qs.filter(id__in=enrollments, status='published')

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        learning_area = serializer.validated_data['learning_area']

        if not TeacherAssignment.objects.filter(teacher=user, learning_area=learning_area, is_active=True).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not assigned to teach this Learning Area.")

        serializer.save(school=user.school, author=user)

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
            title=f"Copy of {original.title}",
            description=original.description,
            delivery_mode=original.delivery_mode,
            cloned_from=original,
            status='draft'
        )
        for lesson in original.lessons.all():
            Lesson.objects.create(course=clone, sub_strand=lesson.sub_strand, title=lesson.title, content=lesson.content, order=lesson.order, school=original.school)

        return Response(CourseSerializer(clone).data)


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Topic.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            return qs.filter(learning_area__in=TeacherAssignment.objects.filter(
                teacher=user, is_active=True).values_list('learning_area', flat=True))
        if user.role in ['STUDENT', 'PARENT']:
            enrolled_areas = CourseEnrollment.objects.filter(learner=user).values_list(
                'course__learning_area', flat=True)
            return qs.filter(learning_area__in=enrolled_areas, is_published=True)
        return qs

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
            # Learners only see published, currently-visible lessons
            now = timezone.now()
            qs = qs.filter(is_published=True).filter(
                Q(publish_at__isnull=True) | Q(publish_at__lte=now))
        return qs

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored.")
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit lessons in courses you authored.")
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
        grade = course.learning_area.grade if course.learning_area else None
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
        if lesson.course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add materials to lessons in courses you authored.")
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.lesson.course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit materials in courses you authored.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.lesson.course.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete materials in courses you authored.")
        instance.delete()
