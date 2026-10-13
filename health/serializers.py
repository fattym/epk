from rest_framework import serializers

from .models import HealthRecord, NurseVisit


class NurseVisitSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = NurseVisit
        fields = [
            'id', 'school', 'student', 'student_name', 'health_record',
            'reason', 'treatment', 'medication_given', 'severity',
            'recorded_by', 'parent_notified', 'created_at',
        ]
        read_only_fields = ['id', 'school', 'recorded_by', 'created_at']

    def get_student_name(self, obj):
        return f'{obj.student.first_name} {obj.student.last_name}'


class HealthRecordSerializer(serializers.ModelSerializer):
    visits = NurseVisitSerializer(many=True, read_only=True)

    class Meta:
        model = HealthRecord
        fields = [
            'id', 'school', 'student', 'allergies', 'medications',
            'medical_conditions', 'emergency_contact_name',
            'emergency_contact_phone', 'last_updated', 'created_at',
            'visits',
        ]
        read_only_fields = ['id', 'school', 'last_updated', 'created_at']
