from django.contrib import admin
from .models import User, ParentLearner, StudentProfile, TeacherProfile


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'school', 'is_active']
    list_filter = ['role', 'school', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']

    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == 'STUDENT':
                return [StudentProfileInline]
            elif obj.role == 'TEACHER':
                return [TeacherProfileInline]
        return []


@admin.register(ParentLearner)
class ParentLearnerAdmin(admin.ModelAdmin):
    list_display = ['parent', 'learner', 'relationship', 'school']
    list_filter = ['school', 'relationship']
    search_fields = ['parent__email', 'learner__email']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nemis_number', 'assessment_number', 'school']
    search_fields = ['user__email', 'nemis_number', 'assessment_number']
    list_filter = ['school']


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'national_id', 'school']
    search_fields = ['user__email', 'employee_id', 'national_id']
    list_filter = ['school']
