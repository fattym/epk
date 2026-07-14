from django.contrib import admin
from .models import (
    Grade, Pathway, Stream, LearningArea,
    Strand, SubStrand, LearningOutcome, RubricDescriptor,
    TeacherAssignment, ClassTeacher, Enrollment, Timetable, Assignment, Term,
)

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'stage', 'order']
    list_filter = ['stage']

@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'pathway', 'school']
    list_filter = ['grade', 'pathway', 'school']
    search_fields = ['name']

@admin.register(LearningArea)
class LearningAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'grade', 'pathway', 'school']
    list_filter = ['grade', 'pathway', 'school']
    search_fields = ['name', 'code']

@admin.register(Strand)
class StrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'learning_area']
    list_filter = ['learning_area']
    search_fields = ['name']

@admin.register(SubStrand)
class SubStrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'strand']
    list_filter = ['strand']
    search_fields = ['name']

@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ['description', 'sub_strand']
    list_filter = ['sub_strand__strand__learning_area']
    search_fields = ['description']

@admin.register(RubricDescriptor)
class RubricDescriptorAdmin(admin.ModelAdmin):
    list_display = ['outcome', 'level', 'descriptor_text']
    list_filter = ['level', 'outcome__sub_strand__strand__learning_area']

@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'learning_area', 'stream', 'school']
    list_filter = ['school']
    search_fields = ['teacher__email', 'learning_area__name']

@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ['stream', 'teacher', 'is_primary', 'school']
    list_filter = ['is_primary', 'school']
    search_fields = ['stream__name', 'teacher__email']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'stream', 'enrollment_date', 'is_active', 'school']
    list_filter = ['is_active', 'school', 'stream']
    search_fields = ['student__email', 'stream__name']

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['stream', 'learning_area', 'teacher', 'day_of_week', 'start_time', 'end_time', 'school']
    list_filter = ['day_of_week', 'school']
    search_fields = ['stream__name', 'learning_area__name', 'teacher__email']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'stream', 'learning_area', 'assigned_by', 'due_date', 'school']
    list_filter = ['school', 'due_date']
    search_fields = ['title', 'assigned_by__email']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'start_date', 'end_date', 'school', 'is_current']
    list_filter = ['academic_year', 'is_current', 'school']
    search_fields = ['name', 'academic_year']
