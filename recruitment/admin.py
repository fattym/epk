from django.contrib import admin
from .models import PipelineStage, JobPosting, Candidate, Application, Interview, ScoreCard, Offer


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['school', 'name', 'order', 'is_default']
    list_filter = ['school', 'is_default']
    search_fields = ['name', 'school__name']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['school', 'title', 'department', 'employment_type', 'is_published', 'application_deadline', 'posted_by']
    list_filter = ['school', 'is_published', 'employment_type', 'department']
    search_fields = ['title', 'description', 'department', 'school__name']
    date_hierarchy = 'created_at'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'source', 'created_at']
    list_filter = ['source']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'created_at'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job_posting', 'school', 'status', 'applied_at']
    list_filter = ['status', 'school', 'job_posting__department']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'candidate__email', 'job_posting__title']
    date_hierarchy = 'applied_at'


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'scheduled_at', 'status', 'created_by']
    list_filter = ['status', 'scheduled_at']
    search_fields = ['application__candidate__first_name', 'application__candidate__last_name', 'application__job_posting__title']
    filter_horizontal = ['interviewers']


@admin.register(ScoreCard)
class ScoreCardAdmin(admin.ModelAdmin):
    list_display = ['interview', 'interviewer', 'rating', 'recommendation', 'submitted_at']
    list_filter = ['recommendation', 'rating']
    search_fields = ['interview__application__candidate__first_name', 'interviewer__email']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['application', 'position', 'status', 'start_date', 'expiry_date', 'accepted_at']
    list_filter = ['status', 'start_date', 'expiry_date']
    search_fields = ['position', 'application__candidate__first_name', 'application__candidate__last_name']
