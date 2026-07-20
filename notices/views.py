from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from academics.models import Enrollment
from .models import Notice
from .serializers import NoticeSerializer


def _visible_to(notice, user):
    t = notice.target_type
    if t == 'ALL':
        return True
    if t == user.role:
        return True
    if t == 'STREAM' and notice.target_stream_id:
        return Enrollment.objects.filter(
            student=user, stream_id=notice.target_stream_id, is_active=True
        ).exists()
    if t == 'INDIVIDUAL':
        return notice.target_users.filter(pk=user.pk).exists()
    return False


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notice.objects.filter(school=self.request.user.school)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if request.user.role != 'ADMIN':
            qs = [n for n in qs if _visible_to(n, request.user)]
            qs.sort(key=lambda n: (not n.is_pinned, n.created_at), reverse=True)
            return Response(self.get_serializer(qs, many=True).data)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'detail': 'Only admins manage notices.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'detail': 'Only admins manage notices.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notice = self.get_object()
        notice.read_by.add(request.user)
        return Response({'read': True})
