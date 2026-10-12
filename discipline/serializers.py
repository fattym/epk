from rest_framework import serializers

from .models import DisciplinaryAppeal, DisciplinaryRecord


class DisciplinaryAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplinaryAppeal
        fields = ['id', 'record', 'submitted_by', 'reason', 'status', 'decided_by', 'decided_at', 'created_at']
        read_only_fields = ['id', 'status', 'decided_by', 'decided_at', 'created_at']


class DisciplinaryRecordSerializer(serializers.ModelSerializer):
    appeals = DisciplinaryAppealSerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DisciplinaryRecord
        fields = [
            'id', 'school', 'student', 'student_name', 'incident_type',
            'description', 'action_taken', 'severity', 'recorded_by',
            'recorded_by_name', 'parent_notified', 'resolved',
            'created_at', 'appeals',
        ]
        read_only_fields = ['id', 'school', 'recorded_by', 'created_at']

    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return f'{obj.recorded_by.first_name} {obj.recorded_by.last_name}'
        return None
