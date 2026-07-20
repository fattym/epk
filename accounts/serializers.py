from rest_framework import serializers
from .models import User, ParentLearner, StudentProfile, TeacherProfile


class ParentLearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentLearner
        fields = ['id', 'parent', 'learner', 'school', 'relationship', 'created_at']
        read_only_fields = ['id', 'created_at', 'school']


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        exclude = ['user', 'school']


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        exclude = ['user', 'school']


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(required=False)
    teacher_profile = TeacherProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'address', 'date_of_birth', 'school', 'created_at', 'tsc_number', 'qualification', 'subject_specializations', 'student_profile', 'teacher_profile']
        read_only_fields = ['id', 'created_at']

    def update(self, instance, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        teacher_profile_data = validated_data.pop('teacher_profile', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if instance.role == 'STUDENT' and student_profile_data is not None:
            profile, created = StudentProfile.objects.get_or_create(user=instance, defaults={'school': instance.school})
            for attr, value in student_profile_data.items():
                setattr(profile, attr, value)
            profile.save()
            
        elif instance.role == 'TEACHER' and teacher_profile_data is not None:
            profile, created = TeacherProfile.objects.get_or_create(user=instance, defaults={'school': instance.school})
            for attr, value in teacher_profile_data.items():
                setattr(profile, attr, value)
            profile.save()
            
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    student_profile = StudentProfileSerializer(required=False)
    teacher_profile = TeacherProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'role', 'phone',
            'address', 'date_of_birth', 'school', 'tsc_number', 'qualification',
            'subject_specializations', 'student_profile', 'teacher_profile'
        ]

    def create(self, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        teacher_profile_data = validated_data.pop('teacher_profile', None)
        
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        if user.role == 'STUDENT':
            profile_data = student_profile_data or {}
            StudentProfile.objects.create(user=user, school=user.school, **profile_data)
        elif user.role == 'TEACHER':
            profile_data = teacher_profile_data or {}
            TeacherProfile.objects.create(user=user, school=user.school, **profile_data)
            
        return user
