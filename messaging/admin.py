from django.contrib import admin
from .models import (
    Announcement, DirectMessage, Notification,
    Conversation, ConversationParticipant, ConversationMessage,
)


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


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'conversation_type', 'group_target', 'school', 'created_by', 'created_at']
    list_filter = ['conversation_type', 'group_target', 'school', 'created_at']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'unread_count', 'joined_at']
    list_filter = ['conversation__school', 'joined_at']


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'sent_at']
    list_filter = ['conversation__school', 'sent_at']
