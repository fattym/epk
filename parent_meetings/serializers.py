from rest_framework import serializers

from .models import MeetingNote, ParentTeacherMeeting


class MeetingNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = MeetingNote
        fields = ['id', 'meeting', 'author', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        return f'{obj.author.first_name} {obj.author.last_name}'


class ParentTeacherMeetingSerializer(serializers.ModelSerializer):
    notes = MeetingNoteSerializer(many=True, read_only=True)
    teacher_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ParentTeacherMeeting
        fields = [
            'id', 'school', 'teacher', 'teacher_name', 'parent', 'parent_name',
            'student', 'student_name', 'scheduled_at', 'duration_minutes',
            'location', 'agenda', 'status', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def get_teacher_name(self, obj):
        return f'{obj.teacher.first_name} {obj.teacher.last_name}'

    def get_parent_name(self, obj):
        return f'{obj.parent.first_name} {obj.parent.last_name}'

    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'


class ParentTeacherMeetingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentTeacherMeeting
        fields = [
            'id', 'teacher', 'parent', 'student', 'scheduled_at',
            'duration_minutes', 'location', 'agenda', 'status',
        ]
        read_only_fields = ['id']
