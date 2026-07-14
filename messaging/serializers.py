from rest_framework import serializers
from .models import Announcement, DirectMessage, Notification


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'content',
            'target_audience',
            'created_by',
            'school',
            'created_at',
            'is_published',
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'school']


class DirectMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectMessage
        fields = [
            'id',
            'sender',
            'recipient',
            'subject',
            'content',
            'is_read',
            'sent_at',
            'school',
        ]
        read_only_fields = ['id', 'sent_at', 'sender', 'school']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'title',
            'message',
            'is_read',
            'created_at',
            'school',
        ]
        read_only_fields = ['id', 'created_at', 'recipient', 'school']
