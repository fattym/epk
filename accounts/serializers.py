from rest_framework import serializers
from .models import User, ParentLearner, StudentProfile, TeacherProfile, TeacherLeave, PasswordReset


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        exclude = ['user', 'school']


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        exclude = ['user', 'school']


class TeacherLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherLeave
        fields = '__all__'
        read_only_fields = ['school', 'created_at', 'updated_at', 'approval_date']


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(required=False)
    teacher_profile = TeacherProfileSerializer(required=False)
    current_grade = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'address', 'date_of_birth', 'school', 'created_at', 'tsc_number', 'qualification', 'subject_specializations', 'student_profile', 'teacher_profile', 'is_active', 'last_login', 'current_grade']
        read_only_fields = ['id', 'created_at', 'last_login']

    def get_current_grade(self, obj):
        if getattr(obj, 'role', None) != 'STUDENT':
            return None
        enrollment = (
            obj.enrollments
            .filter(is_active=True)
            .select_related('stream__grade')
            .first()
        )
        if not enrollment or not enrollment.stream:
            return None
        stream = enrollment.stream
        grade_name = getattr(stream.grade, 'name', None) if stream.grade else None
        return f'{grade_name} {stream.name}' if grade_name else stream.name


    def update(self, instance, validated_data):
        student_profile_data = validated_data.pop('student_profile', None)
        teacher_profile_data = validated_data.pop('teacher_profile', None)

        m2m_data = {}
        for field in instance._meta.many_to_many:
            if field.name in validated_data:
                m2m_data[field.name] = validated_data.pop(field.name)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for field_name, value in m2m_data.items():
            getattr(instance, field_name).set(value)
        
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


class ParentLearnerSerializer(serializers.ModelSerializer):
    learner = UserSerializer(read_only=True)
    parent = UserSerializer(read_only=True)

    class Meta:
        model = ParentLearner
        fields = ['id', 'parent', 'learner', 'school', 'relationship', 'created_at']
        read_only_fields = ['id', 'created_at', 'school']


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


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            self.context['user'] = user
        except User.DoesNotExist:
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_token(self, value):
        from django.utils import timezone
        try:
            reset = PasswordReset.objects.get(token=value)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError('Invalid or expired reset token.')
        if not reset.is_valid:
            raise serializers.ValidationError('Invalid or expired reset token.')
        self.context['reset'] = reset
        return value

    def save(self):
        reset = self.context['reset']
        user = reset.user
        user.set_password(self.validated_data['password'])
        user.save()
        reset.used = True
        reset.save()
        return user