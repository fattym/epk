from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from accounts.models import User, ParentLearner
from academics.models import TeacherAssignment, Enrollment
from .models import AttendanceRecord, AttendanceSummary, AttendanceNotification
from .serializers import AttendanceRecordSerializer, AttendanceSummarySerializer, AttendanceNotificationSerializer


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AttendanceRecord.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceRecord.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            qs = qs.filter(stream_id__in=stream_ids)
        elif user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            qs = qs.filter(student_id__in=learner_ids)
        return qs.select_related('student', 'stream', 'recorded_by')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, recorded_by=self.request.user)
        self._maybe_notify(serializer.instance)
        self._regenerate_summary(serializer.instance.student, serializer.instance.stream, serializer.instance.date)

    def perform_update(self, serializer):
        old = self.get_object()
        instance = serializer.save()
        if old.status != instance.status:
            self._maybe_notify(instance)
        self._regenerate_summary(instance.student, instance.stream, instance.date)

    def _maybe_notify(self, record):
        if record.status == 'ABSENT':
            parents = ParentLearner.objects.filter(learner=record.student, school=record.school).values_list('parent', flat=True)
            for parent_id in parents:
                AttendanceNotification.objects.create(
                    student=record.student,
                    school=record.school,
                    notification_type='ABSENT_ALERT',
                    message=f'{record.student.get_full_name() or record.student.email} was marked absent on {record.date} from {record.stream.name}.',
                    sent_to_id=parent_id,
                )

    def _regenerate_summary(self, student, stream, date):
        month = date.month
        year = date.year
        summary, _ = AttendanceSummary.objects.get_or_create(student=student, stream=stream, month=month, year=year, school=student.school)
        qs = AttendanceRecord.objects.filter(student=student, stream=stream, date__month=month, date__year=year, school=student.school)
        agg = qs.aggregate(
            present=Count('id', filter=Q(status='PRESENT')),
            absent=Count('id', filter=Q(status='ABSENT')),
            late=Count('id', filter=Q(status='LATE')),
            excused=Count('id', filter=Q(status__in=['EXCUSED', 'SICK_LEAVE', 'AUTHORIZED_ABSENCE'])),
        )
        summary.present_days = agg['present'] or 0
        summary.absent_days = agg['absent'] or 0
        summary.late_days = agg['late'] or 0
        summary.excused_days = agg['excused'] or 0
        summary.save()

    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        user = request.user
        if user.role not in ['TEACHER', 'ADMIN']:
            return Response({'detail': 'Only teachers and admins can mark attendance.'}, status=status.HTTP_403_FORBIDDEN)

        stream_id = request.data.get('stream')
        date_str = request.data.get('date')
        records = request.data.get('records', [])

        if not stream_id or not date_str or not records:
            return Response({'detail': 'stream, date, and records[] are required.'}, status=status.HTTP_400_BAD_REQUEST)

        from academics.models import Stream
        try:
            stream = Stream.objects.get(id=stream_id, school=user.school)
            date_obj = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (Stream.DoesNotExist, ValueError):
            return Response({'detail': 'Invalid stream or date. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'TEACHER':
            if not TeacherAssignment.objects.filter(teacher=user, stream=stream, is_active=True).exists():
                return Response({'detail': 'You are not assigned to this stream.'}, status=status.HTTP_403_FORBIDDEN)

        created = []
        for item in records:
            student_id = item.get('student')
            status_val = item.get('status', 'PRESENT')
            note = item.get('note', '')
            if not student_id:
                continue
            try:
                student = User.objects.get(id=student_id, role='STUDENT')
            except User.DoesNotExist:
                continue
            if not Enrollment.objects.filter(student=student, stream=stream, is_active=True).exists():
                continue
            record, _ = AttendanceRecord.objects.update_or_create(
                student=student, stream=stream, date=date_obj, school=user.school,
                defaults={'status': status_val, 'note': note, 'recorded_by': user}
            )
            created.append(AttendanceRecordSerializer(record).data)

        return Response({'created': len(created), 'records': created}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        stream_id = request.query_params.get('stream')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        student_id = request.query_params.get('student')

        qs = AttendanceRecord.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            qs = qs.filter(stream_id__in=stream_ids)
        elif user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            qs = qs.filter(student_id__in=learner_ids)

        if stream_id:
            qs = qs.filter(stream_id=stream_id)
        if student_id:
            qs = qs.filter(student_id=student_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        data = qs.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT')),
            absent=Count('id', filter=Q(status='ABSENT')),
            late=Count('id', filter=Q(status='LATE')),
            excused=Count('id', filter=Q(status__in=['EXCUSED', 'SICK_LEAVE', 'AUTHORIZED_ABSENCE'])),
        )
        return Response(data)

    @action(detail=False, methods=['get'])
    def monthly_trend(self, request):
        user = request.user
        stream_id = request.query_params.get('stream')
        year = request.query_params.get('year') or timezone.now().year

        qs = AttendanceRecord.objects.filter(school=user.school, date__year=year)
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            qs = qs.filter(stream_id__in=stream_ids)
        elif user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            qs = qs.filter(student_id__in=learner_ids)

        if stream_id:
            qs = qs.filter(stream_id=stream_id)

        trend = []
        for month in range(1, 13):
            recs = qs.filter(date__month=month)
            agg = recs.aggregate(
                total=Count('id'),
                present=Count('id', filter=Q(status='PRESENT')),
                absent=Count('id', filter=Q(status='ABSENT')),
                excused=Count('id', filter=Q(status__in=['EXCUSED', 'SICK_LEAVE', 'AUTHORIZED_ABSENCE'])),
            )
            pct = round((agg['present'] / agg['total'] * 100), 1) if agg['total'] else 0
            trend.append({'month': month, 'total': agg['total'], 'present': agg['present'], 'absent': agg['absent'], 'excused': agg['excused'], 'attendance_pct': pct})
        return Response(trend)

    @action(detail=False, methods=['get'])
    def class_list(self, request):
        user = request.user
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            from academics.models import Stream
            streams = Stream.objects.filter(id__in=stream_ids).select_related('grade')
        else:
            from academics.models import Stream
            streams = Stream.objects.filter(school=user.school).select_related('grade')
        data = [{'id': s.id, 'name': s.name, 'grade': s.grade.name if s.grade else ''} for s in streams]
        return Response(data)

    @action(detail=False, methods=['post'])
    def regenerate_summaries(self, request):
        user = request.user
        if user.role not in ['TEACHER', 'ADMIN']:
            return Response({'detail': 'Only teachers and admins can regenerate summaries.'}, status=status.HTTP_403_FORBIDDEN)
        month = int(request.data.get('month') or timezone.now().month)
        year = int(request.data.get('year') or timezone.now().year)
        stream_id = request.data.get('stream')
        qs = AttendanceRecord.objects.filter(school=user.school, date__month=month, date__year=year)
        if stream_id:
            qs = qs.filter(stream_id=stream_id)
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            qs = qs.filter(stream_id__in=stream_ids)
        groups = qs.values('student', 'stream').annotate(
            present=Count('id', filter=Q(status='PRESENT')),
            absent=Count('id', filter=Q(status='ABSENT')),
            late=Count('id', filter=Q(status='LATE')),
            excused=Count('id', filter=Q(status__in=['EXCUSED', 'SICK_LEAVE', 'AUTHORIZED_ABSENCE'])),
        )
        updated = 0
        for g in groups:
            summary, _ = AttendanceSummary.objects.get_or_create(
                student_id=g['student'], stream_id=g['stream'], month=month, year=year, school=user.school,
            )
            summary.present_days = g['present'] or 0
            summary.absent_days = g['absent'] or 0
            summary.late_days = g['late'] or 0
            summary.excused_days = g['excused'] or 0
            summary.save()
            updated += 1
        return Response({'updated': updated, 'month': month, 'year': year})

    @action(detail=False, methods=['get'])
    def students_for_stream(self, request):
        user = request.user
        stream_id = request.query_params.get('stream')
        if not stream_id:
            return Response({'detail': 'stream query param is required.'}, status=status.HTTP_400_BAD_REQUEST)
        from academics.models import Stream
        try:
            stream = Stream.objects.get(id=stream_id, school=user.school)
        except Stream.DoesNotExist:
            return Response({'detail': 'Stream not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user.role == 'TEACHER':
            if not TeacherAssignment.objects.filter(teacher=user, stream=stream, is_active=True).exists():
                return Response({'detail': 'You are not assigned to this stream.'}, status=status.HTTP_403_FORBIDDEN)
        enrollments = Enrollment.objects.filter(stream=stream, is_active=True).select_related('student')
        data = []
        for e in enrollments:
            data.append({
                'id': e.student.id,
                'student_id': e.student.student_profile.admission_number if hasattr(e.student, 'student_profile') and e.student.student_profile else '',
                'name': f"{e.student.first_name or ''} {e.student.last_name or ''}".strip() or e.student.email,
                'email': e.student.email,
            })
        return Response(data)


class AttendanceSummaryViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AttendanceSummary.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceSummary.objects.filter(school=user.school)
        if user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            qs = qs.filter(stream_id__in=stream_ids)
        elif user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            qs = qs.filter(student_id__in=learner_ids)
        return qs.select_related('student', 'stream')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class AttendanceNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AttendanceNotification.objects.none()

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceNotification.objects.filter(school=user.school)
        if user.role == 'PARENT':
            qs = qs.filter(sent_to=user)
        elif user.role == 'STUDENT':
            qs = qs.filter(student=user)
        elif user.role == 'TEACHER':
            stream_ids = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list('stream_id', flat=True)
            student_ids = Enrollment.objects.filter(stream_id__in=stream_ids).values_list('student_id', flat=True)
            qs = qs.filter(student_id__in=student_ids)
        return qs.select_related('student', 'sent_to')

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'detail': 'Marked as read.'})