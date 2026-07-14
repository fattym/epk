from rest_framework import serializers
from .models import School, SchoolSettings


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'code', 'address', 'phone', 'email', 'website', 'logo', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class SchoolSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSettings
        fields = '__all__'
        read_only_fields = ['school']
