from rest_framework import serializers
from .models import User, ParentLearner


class ParentLearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentLearner
        fields = ['id', 'parent', 'learner', 'school', 'relationship', 'created_at']
        read_only_fields = ['id', 'created_at', 'school']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'address', 'date_of_birth', 'school', 'created_at', 'tsc_number', 'qualification', 'subject_specializations']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'role', 'phone',
            'address', 'date_of_birth', 'school', 'tsc_number', 'qualification',
            'subject_specializations',
        ]
