from django.contrib import admin

from .models import MeetingNote, ParentTeacherMeeting


@admin.register(ParentTeacherMeeting)
class ParentTeacherMeetingAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'parent', 'student', 'scheduled_at', 'status', 'school']
    list_filter = ['school', 'status', 'scheduled_at']
    search_fields = ['teacher__email', 'parent__email', 'student__email']
    autocomplete_fields = ['teacher', 'parent', 'student']


@admin.register(MeetingNote)
class MeetingNoteAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'author', 'created_at']
    autocomplete_fields = ['meeting', 'author']
