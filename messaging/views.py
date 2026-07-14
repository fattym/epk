from django.db.models import Q
from rest_framework import viewsets, permissions
from .models import Announcement, DirectMessage, Notification
from .serializers import AnnouncementSerializer, DirectMessageSerializer, NotificationSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Announcement.objects.none()

    def get_queryset(self):
        return Announcement.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)


class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DirectMessage.objects.none()

    def get_queryset(self):
        user = self.request.user
        return DirectMessage.objects.filter(school=user.school).filter(
            Q(sender=user) | Q(recipient=user)
        )

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, school=self.request.user.school)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.none()

    def get_queryset(self):
        return Notification.objects.filter(
            school=self.request.user.school,
            recipient=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)
