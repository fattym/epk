from django.contrib import admin
from .models import User, ParentLearner


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'school', 'is_active']
    list_filter = ['role', 'school', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']


@admin.register(ParentLearner)
class ParentLearnerAdmin(admin.ModelAdmin):
    list_display = ['parent', 'learner', 'relationship', 'school']
    list_filter = ['school', 'relationship']
    search_fields = ['parent__email', 'learner__email']
