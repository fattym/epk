from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from accounts.models import User
from academics.models import LearningOutcome, Term, TeacherAssignment, Enrollment


def teacher_can_assess(user, learner, learning_area, term):
    """True if `user` is an active teacher assigned to `learner`'s stream for `term`,
    either as a class_teacher (whole stream) or as the subject_teacher for `learning_area`."""
    enrollment = Enrollment.objects.filter(student=learner, is_active=True).first()
    if not enrollment:
        return False
    return TeacherAssignment.objects.filter(
        teacher=user,
        stream=enrollment.stream,
        term=term,
        is_active=True,
    ).filter(
        Q(role='class_teacher') | Q(learning_area=learning_area),
    ).exists()


class CompetencyAssessment(models.Model):
    LEVEL_CHOICES = (
        ('BE', 'Below Expectation'),
        ('AE', 'Approaching Expectation'),
        ('ME', 'Meeting Expectation'),
        ('EE', 'Exceeding Expectation'),
    )
    learner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='competency_assessments')
    outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name='assessments')
    level_achieved = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    teacher_comment = models.TextField(blank=True)
    assessed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='given_assessments')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='assessments')
    # Client-generated UUID so offline-first clients can retry syncs idempotently.
    client_uuid = models.UUIDField(unique=True, null=True, blank=True, db_index=True)
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at', 'learner', 'outcome']
        unique_together = ['learner', 'outcome', 'term']

    def clean(self):
        if self.assessed_by_id and self.learner_id and self.outcome_id and self.term_id:
            learning_area = self.outcome.sub_strand.strand.learning_area
            if not teacher_can_assess(self.assessed_by, self.learner, learning_area, self.term):
                raise ValidationError(
                    {'assessed_by': "Teacher is not assigned to this learner's class/subject for this term."}
                )

    def __str__(self):
        return f'{self.learner} - {self.outcome} - {self.get_level_achieved_display()}'


class AssessmentEvidence(models.Model):
    """Supporting evidence for a competency assessment (photo of work, document, audio, video).

    Makes a bare rubric level meaningful to parents and strengthens moderation.
    """
    EVIDENCE_TYPE_CHOICES = (
        ('photo', 'Photo of Work'),
        ('document', 'Document'),
        ('audio', 'Audio Recording'),
        ('video', 'Video'),
    )
    assessment = models.ForeignKey(CompetencyAssessment, related_name='evidence', on_delete=models.CASCADE)
    file = models.FileField(upload_to='assessment_evidence/%Y/%m/')
    evidence_type = models.CharField(max_length=10, choices=EVIDENCE_TYPE_CHOICES)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Evidence - {self.assessment} ({self.get_evidence_type_display()})'


class LearnerPortfolio(models.Model):
    learner = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='portfolio')
    current_level = models.CharField(max_length=2, choices=CompetencyAssessment.LEVEL_CHOICES, blank=True)
    strengths = models.TextField(blank=True)
    areas_for_growth = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Portfolio - {self.learner}'
