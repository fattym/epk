from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AlumniNetworkEventViewSet, AlumniViewSet

router = DefaultRouter()
router.register(r'alumni', AlumniViewSet, basename='alumni')
router.register(r'events', AlumniNetworkEventViewSet, basename='alumninetworkevent')

urlpatterns = [
    path('', include(router.urls)),
]
