from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LeaveRequestViewSet,
    LeaveTypeViewSet,
    PayrollSettingsViewSet,
    PayslipViewSet,
    StaffProfileViewSet,
)

router = DefaultRouter()
router.register(r'staff-profiles', StaffProfileViewSet, basename='staffprofile')
router.register(r'leave-types', LeaveTypeViewSet, basename='leavetype')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'settings', PayrollSettingsViewSet, basename='payrollsettings')

urlpatterns = [
    path('', include(router.urls)),
]
