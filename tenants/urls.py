from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet, SchoolSettingsViewSet

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)
router.register(r'school-settings', SchoolSettingsViewSet, basename='school-settings')

urlpatterns = [
    path('', include(router.urls)),
]
