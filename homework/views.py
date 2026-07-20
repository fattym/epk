from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from academics.models import Enrollment
from .models import Homework, HomeworkSubmission
from .serializers import HomeworkSerializer, HomeworkSubmissionSerializer


class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Homework.objects.filter(school=self.request.user.school)
        role = self.request.user.role
        if role == 'TEACHER':
            return qs.filter(teacher=self.request.user)
        if role == 'STUDENT':
            enrolled = list(
                Enrollment.objects.filter(
                    student=self.request.user, is_active=True
                ).values_list('stream_id', flat=True)
            )
            return qs.filter(stream_id__in=enrolled)
        return qs  # admin sees everything

    def perform_create(self, serializer):
        homework = serializer.save(school=self.request.user.school, teacher=self.request.user)
        # Pre-create a submission row per enrolled student so the teacher can grade/track.
        students = Enrollment.objects.filter(
            stream=homework.stream, school=homework.school, is_active=True
        ).select_related('student')
        for enr in students:
            HomeworkSubmission.objects.get_or_create(
                homework=homework,
                student=enr.student,
                school=homework.school,
            )

    def _teacher_or_admin(self):
        return self.request.user.role in ['TEACHER', 'ADMIN']

    def update(self, request, *args, **kwargs):
        if not self._teacher_or_admin():
            return Response(
                {'detail': 'Only teachers or admins can edit homework.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._teacher_or_admin():
            return Response(
                {'detail': 'Only teachers or admins can delete homework.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        if not self._teacher_or_admin():
            return Response(
                {'detail': 'Only teachers or admins can grade.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        homework = self.get_object()
        submission_id = request.data.get('submission_id')
        if not submission_id:
            return Response(
                {'detail': 'submission_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission = HomeworkSubmission.objects.filter(
            homework=homework, id=submission_id
        ).first()
        if not submission:
            return Response(
                {'detail': 'Submission not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if 'marks' in request.data and request.data['marks'] not in (None, ''):
            try:
                submission.marks = Decimal(str(request.data['marks']))
            except (InvalidOperation, ValueError):
                return Response(
                    {'detail': 'Marks must be a number.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if 'feedback' in request.data:
            submission.feedback = request.data['feedback']
        if 'status' in request.data:
            submission.status = request.data['status']
        submission.save()
        return Response(HomeworkSubmissionSerializer(submission).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        if self.request.user.role != 'STUDENT':
            return Response(
                {'detail': 'Only students submit homework.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        homework = self.get_object()
        submission = HomeworkSubmission.objects.filter(
            homework=homework, student=self.request.user
        ).first()
        if not submission:
            return Response(
                {'detail': 'No submission record for you.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        submission.file_url = request.data.get('file_url', submission.file_url)
        submission.status = 'Late' if timezone.now().date() > homework.due_date else 'Submitted'
        submission.submitted_at = timezone.now()
        submission.save()
        return Response(HomeworkSubmissionSerializer(submission).data)
