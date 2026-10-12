from rest_framework import permissions, viewsets

from .models import MeetingNote, ParentTeacherMeeting
from .serializers import (
    MeetingNoteSerializer,
    ParentTeacherMeetingCreateSerializer,
    ParentTeacherMeetingSerializer,
)


class ParentTeacherMeetingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ParentTeacherMeetingCreateSerializer
        return ParentTeacherMeetingSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'TEACHER':
            return ParentTeacherMeeting.objects.filter(teacher=user).select_related('teacher', 'parent', 'student')
        if user.role == 'PARENT':
            return ParentTeacherMeeting.objects.filter(parent=user).select_related('teacher', 'parent', 'student')
        return ParentTeacherMeeting.objects.filter(school=user.school).select_related('teacher', 'parent', 'student')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class MeetingNoteViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MeetingNote.objects.filter(meeting__school=self.request.user.school).select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
