from rest_framework import permissions, viewsets

from .models import DisciplinaryAppeal, DisciplinaryRecord
from .serializers import DisciplinaryAppealSerializer, DisciplinaryRecordSerializer


class DisciplinaryRecordViewSet(viewsets.ModelViewSet):
    serializer_class = DisciplinaryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DisciplinaryRecord.objects.filter(school=self.request.user.school).select_related('student', 'recorded_by')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, recorded_by=self.request.user)


class DisciplinaryAppealViewSet(viewsets.ModelViewSet):
    serializer_class = DisciplinaryAppealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DisciplinaryAppeal.objects.filter(record__school=self.request.user.school).select_related('record', 'submitted_by')

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
