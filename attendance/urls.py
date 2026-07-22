from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceRecordViewSet, AttendanceSummaryViewSet, AttendanceNotificationViewSet

router = DefaultRouter()
router.register(r'attendance-records', AttendanceRecordViewSet)
router.register(r'attendance-summaries', AttendanceSummaryViewSet)
router.register(r'attendance-notifications', AttendanceNotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]