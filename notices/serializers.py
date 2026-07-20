from rest_framework import serializers
from accounts.models import User
from academics.models import Enrollment
from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    target_stream_name = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    total_audience = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            'id', 'title', 'content', 'target_type', 'target_stream',
            'target_stream_name', 'target_users', 'is_pinned', 'is_published',
            'created_by', 'created_by_name', 'school', 'created_at',
            'read_count', 'total_audience',
        ]
        read_only_fields = [
            'id', 'created_by', 'created_by_name', 'school',
            'created_at', 'target_stream_name', 'read_count', 'total_audience',
        ]

    def get_target_stream_name(self, obj):
        return obj.target_stream.name if obj.target_stream else None

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        u = obj.created_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_read_count(self, obj):
        return obj.read_by.count()

    def get_total_audience(self, obj):
        if obj.target_type == 'STREAM' and obj.target_stream_id:
            return Enrollment.objects.filter(stream_id=obj.target_stream_id, is_active=True).count()
        if obj.target_type == 'INDIVIDUAL':
            return obj.target_users.count()
        if obj.target_type == 'ALL':
            return User.objects.filter(school=obj.school).count()
        return User.objects.filter(school=obj.school, role=obj.target_type).count()
