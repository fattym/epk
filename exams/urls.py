from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, ExamGradeViewSet, ReportCardViewSet, CBCReportCardView

router = DefaultRouter()
router.register(r'exams', ExamViewSet)
router.register(r'grades', ExamGradeViewSet)
router.register(r'report-cards', ReportCardViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('report-cards/cbc/<int:student_id>/', CBCReportCardView.as_view(), name='cbc-report-card'),
    path('report-cards/cbc/', CBCReportCardView.as_view(), name='cbc-report-card-current-user'),
]
