from django.contrib import admin
from .models import CompetencyAssessment, LearnerPortfolio


@admin.register(CompetencyAssessment)
class CompetencyAssessmentAdmin(admin.ModelAdmin):
    list_display = ['learner', 'outcome', 'level_achieved', 'assessed_by', 'term', 'assessed_at']
    list_filter = ['level_achieved', 'term', 'assessed_by']
    search_fields = ['learner__email', 'outcome__description']


@admin.register(LearnerPortfolio)
class LearnerPortfolioAdmin(admin.ModelAdmin):
    list_display = ['learner', 'current_level', 'updated_at']
    list_filter = ['current_level']
    search_fields = ['learner__email']
