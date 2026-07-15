from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PipelineStageViewSet,
    JobPostingViewSet,
    PublicApplicationViewSet,
    ApplicationViewSet,
    InterviewViewSet,
    ScoreCardViewSet,
    OfferViewSet,
)

router = DefaultRouter()
router.register(r'pipeline-stages', PipelineStageViewSet, basename='pipelinestage')
router.register(r'job-postings', JobPostingViewSet, basename='jobposting')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'score-cards', ScoreCardViewSet, basename='scorecard')
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    path('', include(router.urls)),
    path('public/apply/', PublicApplicationViewSet.as_view({'post': 'create'})),
]
