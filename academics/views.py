from rest_framework import viewsets, permissions
from .models import (
    Grade, Pathway, Stream, LearningArea, TeacherAssignment, Timetable, Term,
    Strand, SubStrand, LearningOutcome, RubricDescriptor, ClassTeacher, Enrollment, Assignment,
)
from .serializers import (
    GradeSerializer, PathwaySerializer, StreamSerializer, LearningAreaSerializer,
    StrandSerializer, SubStrandSerializer, LearningOutcomeSerializer, RubricDescriptorSerializer,
    TeacherAssignmentSerializer, ClassTeacherSerializer, EnrollmentSerializer,
    TimetableSerializer, AssignmentSerializer, TermSerializer,
)


class SchoolScopedViewSetMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.model.objects.filter(school=self.request.user.school)


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


class SubStrandViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = SubStrand.objects.all()
    serializer_class = SubStrandSerializer


class LearningOutcomeViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = LearningOutcome.objects.all()
    serializer_class = LearningOutcomeSerializer


class RubricDescriptorViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = RubricDescriptor.objects.all()
    serializer_class = RubricDescriptorSerializer


class TeacherAssignmentViewSet(SchoolScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


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
