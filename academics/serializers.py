from rest_framework import serializers
from .models import (
    Grade, Pathway, Stream, LearningArea, TeacherAssignment, Timetable, Term,
    Strand, SubStrand, LearningOutcome, RubricDescriptor, ClassTeacher, Enrollment, Assignment,
    LearnerGroup,
)


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


class PathwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pathway
        fields = '__all__'


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'


class LearningAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningArea
        fields = '__all__'


class StrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strand
        fields = '__all__'


class SubStrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubStrand
        fields = '__all__'


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = '__all__'


class RubricDescriptorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubricDescriptor
        fields = '__all__'


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAssignment
        fields = '__all__'
        read_only_fields = ['school']


class ClassTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassTeacher
        fields = '__all__'
        read_only_fields = ['school']


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['school']


class TimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = '__all__'
        read_only_fields = ['school']


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ['school', 'assigned_by']


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = '__all__'


class LearnerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerGroup
        fields = '__all__'
        read_only_fields = ['school', 'created_by']
