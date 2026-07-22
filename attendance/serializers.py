from rest_framework import serializers
from accounts.serializers import UserSerializer
from academics.serializers import StreamSerializer
from .models import AttendanceRecord, AttendanceSummary, AttendanceNotification


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    stream_detail = StreamSerializer(source='stream', read_only=True)
    recorded_by_detail = UserSerializer(source='recorded_by', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'student', 'stream', 'date', 'status', 'note', 'recorded_by', 'school', 'student_detail', 'stream_detail', 'recorded_by_detail']
        read_only_fields = ['school', 'recorded_by']


class AttendanceSummarySerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    stream_detail = StreamSerializer(source='stream', read_only=True)
    attendance_percentage = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSummary
        fields = ['id', 'student', 'stream', 'month', 'year', 'present_days', 'absent_days', 'late_days', 'excused_days', 'school', 'student_detail', 'stream_detail', 'attendance_percentage']
        read_only_fields = ['school']

    def get_attendance_percentage(self, obj):
        total = obj.present_days + obj.absent_days + obj.late_days + obj.excused_days
        if total == 0:
            return 100.0
        return round((obj.present_days / total) * 100, 1)


class AttendanceNotificationSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    sent_to_detail = UserSerializer(source='sent_to', read_only=True)

    class Meta:
        model = AttendanceNotification
        fields = ['id', 'student', 'school', 'notification_type', 'message', 'sent_to', 'is_read', 'created_at', 'student_detail', 'sent_to_detail']
        read_only_fields = ['school', 'created_at']