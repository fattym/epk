from rest_framework import permissions, viewsets

from .models import HealthRecord, NurseVisit
from .serializers import HealthRecordSerializer, NurseVisitSerializer


class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HealthRecord.objects.filter(school=self.request.user.school).select_related('student')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class NurseVisitViewSet(viewsets.ModelViewSet):
    serializer_class = NurseVisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NurseVisit.objects.filter(school=self.request.user.school).select_related('student', 'health_record')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, recorded_by=self.request.user)
