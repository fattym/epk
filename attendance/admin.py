from django.contrib import admin
from .models import AttendanceRecord, AttendanceSummary, AttendanceNotification


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'date', 'status', 'note', 'recorded_by', 'school']
    list_filter = ['status', 'date', 'school', 'stream']
    search_fields = ['student__email', 'stream__name', 'note']


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'month', 'year', 'present_days', 'absent_days', 'late_days', 'excused_days', 'school']
    list_filter = ['month', 'year', 'school']
    search_fields = ['student__email', 'stream__name']


@admin.register(AttendanceNotification)
class AttendanceNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notification_type', 'message', 'sent_to', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['student__email', 'message']
