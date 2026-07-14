from django.contrib import admin
from .models import Exam, ExamGrade, ReportCard


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'stream', 'learning_area', 'date', 'start_time', 'end_time', 'total_marks', 'passing_marks', 'school']
    list_filter = ['exam_type', 'stream', 'learning_area', 'date', 'school']


@admin.register(ExamGrade)
class ExamGradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks_obtained', 'grade', 'graded_by', 'school']
    list_filter = ['grade', 'exam', 'school']


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'term', 'total_marks', 'obtained_marks', 'percentage', 'grade', 'generated_at', 'school']
    list_filter = ['term', 'grade', 'stream', 'school']
