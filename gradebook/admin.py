from django.contrib import admin

from .models import (
    CoreCompetency,
    CoreValue,
    StudentBio,
    LearningAreaScore,
    StudentCompetencyScore,
    StudentValueScore,
    PortfolioArtifact,
    AttendanceSummary,
    CycleMeta,
)


@admin.register(CoreCompetency)
class CoreCompetencyAdmin(admin.ModelAdmin):
    list_display = ["order", "code", "name"]
    ordering = ["order"]


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ["order", "name"]
    ordering = ["order"]


@admin.register(StudentBio)
class StudentBioAdmin(admin.ModelAdmin):
    list_display = ["student", "sen_status", "parent_phone"]
    raw_id_fields = ["student"]


@admin.register(LearningAreaScore)
class LearningAreaScoreAdmin(admin.ModelAdmin):
    list_display = ["student", "learning_area", "term", "strand1", "strand2", "strand3", "csl_score"]
    list_filter = ["term", "learning_area"]
    raw_id_fields = ["student"]


@admin.register(StudentCompetencyScore)
class StudentCompetencyScoreAdmin(admin.ModelAdmin):
    list_display = ["student", "competency", "term", "score"]
    list_filter = ["term", "competency"]
    raw_id_fields = ["student"]


@admin.register(StudentValueScore)
class StudentValueScoreAdmin(admin.ModelAdmin):
    list_display = ["student", "value", "term", "level"]
    list_filter = ["term", "value"]
    raw_id_fields = ["student"]


@admin.register(PortfolioArtifact)
class PortfolioArtifactAdmin(admin.ModelAdmin):
    list_display = ["student", "term", "title", "artifact_type", "rating", "uploaded_at"]
    list_filter = ["term", "rating"]
    raw_id_fields = ["student"]


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ["student", "term", "days_present", "days_total", "percentage"]
    list_filter = ["term"]
    raw_id_fields = ["student"]


@admin.register(CycleMeta)
class CycleMetaAdmin(admin.ModelAdmin):
    list_display = ["term", "homeroom_teacher"]
    list_select_related = ["term"]
