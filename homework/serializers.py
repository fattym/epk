from rest_framework import serializers
from .models import Homework, HomeworkSubmission


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkSubmission
        fields = [
            'id', 'homework', 'student', 'student_name', 'file_url',
            'status', 'marks', 'feedback', 'submitted_at', 'created_at',
        ]
        read_only_fields = ['id', 'homework', 'student', 'student_name', 'submitted_at', 'created_at']

    def get_student_name(self, obj):
        u = obj.student
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class HomeworkSerializer(serializers.ModelSerializer):
    stream_name = serializers.SerializerMethodField()
    learning_area_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    submissions = HomeworkSubmissionSerializer(many=True, read_only=True)
    submitted_count = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = [
            'id', 'title', 'description', 'stream', 'stream_name',
            'learning_area', 'learning_area_name', 'teacher', 'teacher_name',
            'due_date', 'file', 'school', 'created_at', 'submissions', 'submitted_count',
        ]
        read_only_fields = [
            'id', 'teacher', 'school', 'created_at', 'stream_name',
            'learning_area_name', 'teacher_name', 'submissions', 'submitted_count',
        ]

    def get_stream_name(self, obj):
        return obj.stream.name if obj.stream else None

    def get_learning_area_name(self, obj):
        if not obj.learning_area:
            return None
        return f'{obj.learning_area.name} ({obj.learning_area.code})'

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        u = obj.teacher
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_submitted_count(self, obj):
        return obj.submissions.filter(status__in=['Submitted', 'Late']).count()
