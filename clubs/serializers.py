from rest_framework import serializers
from .models import Club, ClubSession


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'trainers', 'is_active', 'school', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']


class ClubSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubSession
        fields = ['id', 'club', 'trainer', 'date', 'topic', 'notes', 'attendees', 'school', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']
