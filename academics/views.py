from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Grade, Pathway, Stream, LearningArea, TeacherAssignment, Timetable, Term,
    Strand, SubStrand, LearningOutcome, RubricDescriptor, ClassTeacher, Enrollment, Assignment,
    LearnerGroup,
)
from .serializers import (
    GradeSerializer, PathwaySerializer, StreamSerializer, LearningAreaSerializer,
    StrandSerializer, SubStrandSerializer, LearningOutcomeSerializer, RubricDescriptorSerializer,
    TeacherAssignmentSerializer, ClassTeacherSerializer, EnrollmentSerializer,
    TimetableSerializer, AssignmentSerializer, TermSerializer, LearnerGroupSerializer,
)


class SchoolScopedViewSetMixin:
    permission_classes = [permissions.IsAuthenticated]
    school_filter_field = 'school'

    def get_queryset(self):
        return self.queryset.model.objects.filter(**{self.school_filter_field: self.request.user.school})


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]


class PathwayViewSet(viewsets.ModelViewSet):
    queryset = Pathway.objects.all()
    serializer_class = PathwaySerializer
    permission_classes = [permissions.IsAuthenticated]


class StreamViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer


class LearningAreaViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningArea.objects.all()
    serializer_class = LearningAreaSerializer


class StrandViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Strand.objects.all()
    serializer_class = StrandSerializer
    school_filter_field = 'learning_area__school'


class SubStrandViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = SubStrand.objects.all()
    serializer_class = SubStrandSerializer
    school_filter_field = 'strand__learning_area__school'


class LearningOutcomeViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningOutcome.objects.all()
    serializer_class = LearningOutcomeSerializer
    school_filter_field = 'sub_strand__strand__learning_area__school'


class RubricDescriptorViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = RubricDescriptor.objects.all()
    serializer_class = RubricDescriptorSerializer
    school_filter_field = 'outcome__sub_strand__strand__learning_area__school'


class TeacherAssignmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def my_teachers(self, request):
        user = request.user
        student_id = request.query_params.get('student_id')

        if user.role == 'PARENT':
            from accounts.models import ParentLearner
            if student_id:
                if not ParentLearner.objects.filter(parent=user, learner_id=student_id).exists():
                    return Response({'detail': 'Not authorized.'}, status=403)
                enrollments = Enrollment.objects.filter(student_id=student_id, is_active=True)
            else:
                learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
                enrollments = Enrollment.objects.filter(student_id__in=learner_ids, is_active=True)
        elif user.role == 'STUDENT':
            enrollments = Enrollment.objects.filter(student=user, is_active=True)
        else:
            return Response({'detail': 'Not applicable.'}, status=400)

        stream_ids = enrollments.values_list('stream_id', flat=True)
        assignments = self.get_queryset().filter(stream_id__in=stream_ids, is_active=True)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_students(self, request):
        user = request.user
        if user.role != 'TEACHER':
            return Response({'detail': 'Only teachers can access this.'}, status=403)
            
        assignments = self.get_queryset().filter(teacher=user, is_active=True)
        stream_ids = assignments.values_list('stream_id', flat=True)
        enrollments = Enrollment.objects.filter(stream_id__in=stream_ids, is_active=True)
        
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)



class ClassTeacherViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ClassTeacher.objects.all()
    serializer_class = ClassTeacherSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class EnrollmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class TimetableViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AssignmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, assigned_by=self.request.user)


class TermViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Term.objects.all()
    serializer_class = TermSerializer


class LearnerGroupViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearnerGroup.objects.all()
    serializer_class = LearnerGroupSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, created_by=self.request.user)
