from django.contrib import admin

from .models import Alumni, AlumniNetworkEvent


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'graduation_year', 'school', 'email', 'is_willing_to_mentor']
    list_filter = ['school', 'graduation_year', 'is_willing_to_mentor', 'is_willing_to_be_mentored']
    search_fields = ['first_name', 'last_name', 'email', 'current_institution', 'current_employer']
    autocomplete_fields = ['user']


@admin.register(AlumniNetworkEvent)
class AlumniNetworkEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'school']
    list_filter = ['school', 'event_date']
    filter_horizontal = ['alumni_attendees']
