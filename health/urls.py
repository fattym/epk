from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HealthRecordViewSet, NurseVisitViewSet

router = DefaultRouter()
router.register(r'records', HealthRecordViewSet, basename='healthrecord')
router.register(r'visits', NurseVisitViewSet, basename='nursevisit')

urlpatterns = [
    path('', include(router.urls)),
]
