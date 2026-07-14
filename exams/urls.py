from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, ExamGradeViewSet, ReportCardViewSet

router = DefaultRouter()
router.register(r'exams', ExamViewSet)
router.register(r'grades', ExamGradeViewSet)
router.register(r'report-cards', ReportCardViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
