from django.contrib import admin

from .models import HealthRecord, NurseVisit


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'school', 'emergency_contact_name', 'last_updated']
    list_filter = ['school']
    search_fields = ['student__email', 'student__first_name', 'student__last_name']
    autocomplete_fields = ['student']


@admin.register(NurseVisit)
class NurseVisitAdmin(admin.ModelAdmin):
    list_display = ['student', 'school', 'severity', 'created_at', 'parent_notified']
    list_filter = ['school', 'severity', 'parent_notified', 'created_at']
    search_fields = ['student__email', 'reason']
    autocomplete_fields = ['student', 'health_record']
