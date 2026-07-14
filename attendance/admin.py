from django.contrib import admin
from .models import AttendanceRecord, AttendanceSummary


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'date', 'status', 'recorded_by', 'school']
    list_filter = ['status', 'date', 'school']
    search_fields = ['student__email', 'stream__name']


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'month', 'year', 'present_days', 'absent_days', 'late_days', 'school']
    list_filter = ['month', 'year', 'school']
    search_fields = ['student__email', 'stream__name']
