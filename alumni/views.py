from rest_framework import permissions, viewsets

from .models import Alumni, AlumniNetworkEvent
from .serializers import AlumniCreateSerializer, AlumniNetworkEventSerializer, AlumniSerializer


class AlumniViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AlumniCreateSerializer
        return AlumniSerializer

    def get_queryset(self):
        return Alumni.objects.filter(school=self.request.user.school).select_related('user')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AlumniNetworkEventViewSet(viewsets.ModelViewSet):
    serializer_class = AlumniNetworkEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlumniNetworkEvent.objects.filter(school=self.request.user.school).prefetch_related('alumni_attendees')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)
