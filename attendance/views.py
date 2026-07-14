from rest_framework import viewsets, permissions
from .models import AttendanceRecord, AttendanceSummary
from .serializers import AttendanceRecordSerializer, AttendanceSummarySerializer


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AttendanceRecord.objects.none()

    def get_queryset(self):
        return AttendanceRecord.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AttendanceSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AttendanceSummary.objects.none()

    def get_queryset(self):
        return AttendanceSummary.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)