from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequiredItemViewSet, RequiredItemOptionViewSet, PublicRequiredItemViewSet

router = DefaultRouter()
router.register(r'items', RequiredItemViewSet, basename='requireditem')
router.register(r'options', RequiredItemOptionViewSet, basename='requireditemoption')

urlpatterns = [
    path('', include(router.urls)),
    path('public/', PublicRequiredItemViewSet.as_view({'get': 'list'}), name='public-required-items'),
    path('public/learner/<int:learner_id>/', PublicRequiredItemViewSet.as_view({'get': 'list'}), name='public-required-items-learner'),
]
