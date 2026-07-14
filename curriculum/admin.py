from django.contrib import admin
from .models import ReferenceDocument, SchemeOfWork, SchemeWeek


@admin.register(ReferenceDocument)
class ReferenceDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'learning_area', 'uploaded_by', 'school', 'uploaded_at']
    list_filter = ['document_type', 'school', 'learning_area']
    search_fields = ['title', 'source_note']


@admin.register(SchemeOfWork)
class SchemeOfWorkAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'learning_area', 'term', 'stream', 'status', 'updated_at']
    list_filter = ['status', 'term', 'stream', 'school']
    search_fields = ['teacher__email', 'learning_area__name']


@admin.register(SchemeWeek)
class SchemeWeekAdmin(admin.ModelAdmin):
    list_display = ['scheme', 'week_number', 'strand', 'sub_strand']
    list_filter = ['scheme', 'week_number']
