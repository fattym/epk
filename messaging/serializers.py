from rest_framework import serializers
from accounts.models import User
from .models import (
    Announcement, DirectMessage, Notification,
    Conversation, ConversationParticipant, ConversationMessage,
)


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone']


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


class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    is_group = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'name',
            'conversation_type',
            'group_target',
            'created_by',
            'school',
            'created_at',
            'is_group',
            'display_name',
            'participants',
            'last_message',
            'unread_count',
        ]
        read_only_fields = ['id', 'created_by', 'school', 'created_at']

    def get_participants(self, obj):
        return UserMiniSerializer(
            [p.user for p in obj.participants.all()],
            many=True,
            context=self.context,
        ).data

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return ConversationMessageSerializer(msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        user = request.user
        try:
            participation = obj.participants.get(user=user)
            return participation.unread_count
        except ConversationParticipant.DoesNotExist:
            return 0


class ConversationMessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    is_read_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = ConversationMessage
        fields = [
            'id',
            'conversation',
            'sender',
            'content',
            'sent_at',
            'read_by',
            'is_read_by_current_user',
        ]
        read_only_fields = ['id', 'sender', 'sent_at']

    def get_is_read_by_current_user(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        user = request.user
        return obj.read_by.filter(id=user.id).exists()


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    conversation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = ['id', 'conversation', 'user', 'unread_count', 'joined_at']
