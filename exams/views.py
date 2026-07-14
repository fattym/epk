from rest_framework import viewsets, permissions
from .models import Exam, ExamGrade, ReportCard
from .serializers import ExamSerializer, ExamGradeSerializer, ReportCardSerializer


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exam_type', 'stream', 'learning_area', 'date', 'school']

    def get_queryset(self):
        return Exam.objects.filter(school=self.request.user.school)


class ExamGradeViewSet(viewsets.ModelViewSet):
    queryset = ExamGrade.objects.all()
    serializer_class = ExamGradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'exam', 'grade', 'school']

    def get_queryset(self):
        return ExamGrade.objects.filter(school=self.request.user.school)


class ReportCardViewSet(viewsets.ModelViewSet):
    queryset = ReportCard.objects.all()
    serializer_class = ReportCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'stream', 'term', 'school']

    def get_queryset(self):
        return ReportCard.objects.filter(school=self.request.user.school)
