from rest_framework import permissions, viewsets

from .models import LeaveRequest, LeaveType, PayrollSettings, Payslip, StaffProfile


class StaffProfileViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import StaffProfileSerializer
        return StaffProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STAFF':
            return StaffProfile.objects.filter(user=user)
        return StaffProfile.objects.filter(school=user.school).select_related('user')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import LeaveTypeSerializer
        return LeaveTypeSerializer

    def get_queryset(self):
        return LeaveType.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import LeaveRequestSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STAFF':
            return LeaveRequest.objects.filter(staff__user=user)
        return LeaveRequest.objects.filter(staff__school=user.school).select_related('staff', 'leave_type')


class PayslipViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import PayslipSerializer
        return PayslipSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'STAFF':
            return Payslip.objects.filter(staff__user=user)
        return Payslip.objects.filter(staff__school=user.school).select_related('staff')


class PayrollSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import PayrollSettingsSerializer
        return PayrollSettingsSerializer

    def get_queryset(self):
        return PayrollSettings.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)
