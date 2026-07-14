from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompetencyAssessmentViewSet, LearnerPortfolioViewSet

router = DefaultRouter()
router.register(r'assessments', CompetencyAssessmentViewSet)
router.register(r'portfolios', LearnerPortfolioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
