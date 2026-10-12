from django.db import models

from academics.models import LearningArea, Term
from accounts.models import User


class CoreCompetency(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Core Competencies"

    def __str__(self):
        return self.name


class CoreValue(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class StudentBio(models.Model):
    LEVEL_SEN = (
        ("REG", "Regular Learner"),
        ("HEARING", "Hearing Impairment"),
        ("VISUAL", "Visual Impairment"),
        ("GAT", "Gifted & Talented"),
        ("REMEDIAL", "Needs Remedial Support"),
    )
    student = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="gradebook_bio"
    )
    sen_status = models.CharField(
        max_length=20, choices=LEVEL_SEN, default="REG", verbose_name="SEN Status"
    )
    parent_phone = models.CharField(
        max_length=20, blank=True, verbose_name="Parent / Guardian Phone"
    )
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Bio: {self.student}"


class LearningAreaScore(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="la_scores"
    )
    learning_area = models.ForeignKey(
        LearningArea, on_delete=models.CASCADE, related_name="scores"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="learning_area_scores"
    )
    strand1 = models.PositiveSmallIntegerField(default=3)
    strand2 = models.PositiveSmallIntegerField(default=3)
    strand3 = models.PositiveSmallIntegerField(default=3)
    csl_score = models.PositiveSmallIntegerField(
        default=15, verbose_name="CSL / Project Score (0-20)"
    )
    remarks = models.TextField(blank=True)
    teacher_comment = models.TextField(blank=True)

    class Meta:
        unique_together = ["student", "learning_area", "term"]

    def __str__(self):
        return f"{self.student} - {self.learning_area} - {self.term}"


class StudentCompetencyScore(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="competency_scores"
    )
    competency = models.ForeignKey(
        CoreCompetency, on_delete=models.CASCADE, related_name="student_scores"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="competency_scores"
    )
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ["student", "competency", "term"]

    def __str__(self):
        return f"{self.student} - {self.competency} {self.score}"


class StudentValueScore(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="value_scores"
    )
    value = models.ForeignKey(
        CoreValue, on_delete=models.CASCADE, related_name="student_scores"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="value_scores"
    )
    LEVEL_CHOICES = (
        ("BE", "Below Expectation"),
        ("AE", "Approaching Expectation"),
        ("ME", "Meeting Expectation"),
        ("EE", "Exceeding Expectation"),
    )
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default="ME")

    class Meta:
        unique_together = ["student", "value", "term"]

    def __str__(self):
        return f"{self.student} - {self.value} {self.level}"


class PortfolioArtifact(models.Model):
    ARTIFACT_CHOICES = (
        ("document", "Document / Report"),
        ("image", "Photo / Image"),
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="portfolio_artifacts"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="portfolio_artifacts"
    )
    title = models.CharField(max_length=160)
    artifact_type = models.CharField(
        max_length=10, choices=ARTIFACT_CHOICES, default="image"
    )
    rating = models.CharField(max_length=2, choices=StudentValueScore.LEVEL_CHOICES, default="ME")
    uploaded_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at", "id"]

    def __str__(self):
        return f"{self.student} - {self.title}"


class AttendanceSummary(models.Model):
    """Per-student per-term attendance used on the printed report card."""
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="gradebook_attendance_summaries"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="gradebook_attendance_summaries"
    )
    days_present = models.PositiveSmallIntegerField(default=0)
    days_total = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ["student", "term"]

    @property
    def percentage(self):
        return round((self.days_present / (self.days_total or 1)) * 100)

    def __str__(self):
        return f"{self.student} attendance for {self.term}"


class CycleMeta(models.Model):
    """Class-level metadata for an assessment cycle (term): homeroom teacher, etc."""
    term = models.OneToOneField(
        Term, on_delete=models.CASCADE, related_name="cycle_meta"
    )
    homeroom_teacher = models.CharField(
        max_length=120, default="Mr. J. Mwangi", verbose_name="Class Teacher / Tutor"
    )

    def __str__(self):
        return f"Cycle meta: {self.term}"

