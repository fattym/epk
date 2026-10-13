from rest_framework import serializers

from .models import Alumni, AlumniNetworkEvent


class AlumniNetworkEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumniNetworkEvent
        fields = ['id', 'school', 'title', 'description', 'event_date', 'location', 'alumni_attendees', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']


class AlumniSerializer(serializers.ModelSerializer):
    events = AlumniNetworkEventSerializer(many=True, read_only=True)

    class Meta:
        model = Alumni
        fields = [
            'id', 'school', 'user', 'first_name', 'last_name', 'graduation_year',
            'current_status', 'current_institution', 'current_employer',
            'linkedin_url', 'email', 'phone', 'is_willing_to_be_mentored',
            'is_willing_to_mentor', 'created_at', 'updated_at', 'events',
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']


class AlumniCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = [
            'id', 'user', 'first_name', 'last_name', 'graduation_year',
            'current_status', 'current_institution', 'current_employer',
            'linkedin_url', 'email', 'phone', 'is_willing_to_be_mentored',
            'is_willing_to_mentor',
        ]
        read_only_fields = ['id', 'school']
