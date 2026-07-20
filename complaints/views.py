from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Complaint, ComplaintComment
from .serializers import ComplaintSerializer, ComplaintCommentSerializer


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Complaint.objects.filter(school=self.request.user.school)
        # Students only ever see the grievances they raised.
        if self.request.user.role == 'STUDENT':
            return qs.filter(submitted_by=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            school=self.request.user.school,
            submitted_by=self.request.user,
            status='Pending',
        )

    def _admin_only(self):
        return self.request.user.role == 'ADMIN'

    def update(self, request, *args, **kwargs):
        if not self._admin_only():
            return Response(
                {'detail': 'Only admins can edit complaints.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._admin_only():
            return Response(
                {'detail': 'Only admins can delete complaints.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        if not self._admin_only():
            return Response(
                {'detail': 'Only admins can assign complaints.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        complaint = self.get_object()
        complaint.assigned_to_id = request.data.get('assigned_to') or None
        if complaint.status == 'Pending':
            complaint.status = 'In Progress'
        complaint.save()
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        if not self._admin_only():
            return Response(
                {'detail': 'Only admins can resolve complaints.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        complaint = self.get_object()
        complaint.resolution = request.data.get('resolution', '')
        complaint.status = request.data.get('status', 'Resolved')
        complaint.resolved_at = timezone.now()
        complaint.save()
        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        complaint = self.get_object()
        text = (request.data.get('text') or '').strip()
        if not text:
            return Response(
                {'detail': 'Comment text is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comment = ComplaintComment.objects.create(
            complaint=complaint,
            author=request.user,
            text=text,
        )
        return Response(
            ComplaintCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )
