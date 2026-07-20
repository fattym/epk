from rest_framework import serializers
from .models import Complaint, ComplaintComment


class ComplaintCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintComment
        fields = ['id', 'complaint', 'author', 'author_name', 'text', 'created_at']
        read_only_fields = ['id', 'complaint', 'author', 'author_name', 'created_at']

    def get_author_name(self, obj):
        u = obj.author
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class ComplaintSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    comments = ComplaintCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'description', 'category', 'priority', 'status',
            'submitted_by', 'submitted_by_name', 'assigned_to', 'assigned_to_name',
            'resolution', 'school', 'created_at', 'resolved_at', 'comments',
        ]
        read_only_fields = [
            'id', 'submitted_by', 'submitted_by_name', 'assigned_to_name',
            'school', 'created_at', 'resolved_at', 'comments',
        ]

    def get_submitted_by_name(self, obj):
        u = obj.submitted_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return None
        u = obj.assigned_to
        return f'{u.first_name} {u.last_name}'.strip() or u.email
