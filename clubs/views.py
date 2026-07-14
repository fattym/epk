from rest_framework import viewsets, permissions
from .models import Club, ClubSession
from .serializers import ClubSerializer, ClubSessionSerializer


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Club.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class ClubSessionViewSet(viewsets.ModelViewSet):
    queryset = ClubSession.objects.all()
    serializer_class = ClubSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ClubSession.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        # Defaults the trainer to the logged-in user, but allows an explicit override.
        trainer = serializer.validated_data.get('trainer') or self.request.user
        serializer.save(school=self.request.user.school, trainer=trainer)
