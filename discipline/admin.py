from django.contrib import admin

from .models import DisciplinaryAppeal, DisciplinaryRecord


@admin.register(DisciplinaryRecord)
class DisciplinaryRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'school', 'incident_type', 'severity', 'resolved', 'created_at']
    list_filter = ['school', 'incident_type', 'severity', 'resolved', 'created_at']
    search_fields = ['student__email']
    autocomplete_fields = ['student', 'recorded_by']


@admin.register(DisciplinaryAppeal)
class DisciplinaryAppealAdmin(admin.ModelAdmin):
    list_display = ['record', 'submitted_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
