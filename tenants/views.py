from rest_framework import viewsets, permissions
from .models import School, SchoolSettings
from .serializers import SchoolSerializer, SchoolSettingsSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAuthenticated]


class SchoolSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SchoolSettings.objects.filter(school=self.request.user.school)
