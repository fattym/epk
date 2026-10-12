from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompetencyAssessmentViewSet,
    LearnerPortfolioViewSet,
    AssessmentEvidenceViewSet,
    AssessmentTaskViewSet,
    BulkAssessmentView,
)

router = DefaultRouter()
router.register(r'assessments', CompetencyAssessmentViewSet)
router.register(r'tasks', AssessmentTaskViewSet, basename='assessment-task')
router.register(r'portfolios', LearnerPortfolioViewSet)
router.register(r'evidence', AssessmentEvidenceViewSet)

urlpatterns = [
    path('bulk/', BulkAssessmentView.as_view()),
    path('', include(router.urls)),
]
