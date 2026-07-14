from django.contrib import admin
from .models import Announcement, DirectMessage, Notification


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_audience', 'school', 'created_by', 'is_published', 'created_at']
    list_filter = ['target_audience', 'school', 'is_published', 'created_at']


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'recipient', 'school', 'is_read', 'sent_at']
    list_filter = ['school', 'is_read', 'sent_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'school', 'is_read', 'created_at']
    list_filter = ['school', 'is_read', 'created_at']
