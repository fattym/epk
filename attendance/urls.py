from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceRecordViewSet, AttendanceSummaryViewSet

router = DefaultRouter()
router.register(r'attendance-records', AttendanceRecordViewSet)
router.register(r'attendance-summaries', AttendanceSummaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]