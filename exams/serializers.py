from rest_framework import serializers
from .models import Exam, ExamGrade, ReportCard


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'name', 'exam_type', 'stream', 'learning_area', 'date', 'start_time', 'end_time', 'total_marks', 'passing_marks', 'school']
        read_only_fields = ['id']


class ExamGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamGrade
        fields = ['id', 'student', 'exam', 'marks_obtained', 'grade', 'remarks', 'graded_by', 'school']
        read_only_fields = ['id']


class ReportCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCard
        fields = ['id', 'student', 'stream', 'term', 'total_marks', 'obtained_marks', 'percentage', 'grade', 'remarks', 'generated_at', 'school']
        read_only_fields = ['id', 'generated_at']
