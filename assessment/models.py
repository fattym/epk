from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from accounts.models import User
from academics.models import LearningArea, LearningOutcome, Term, TeacherAssignment, Enrollment


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


class AssessmentTask(models.Model):
    """A formative assessment task definition (a task + the students assigned to it).

    Mirrors the template's "Assessment Task Builder" (ASM-XX) entity: a learning
    area, strand/sub-strand, task type, and the per-learner rubric results.
    """
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    )
    TASK_TYPE_CHOICES = (
        ('PPT', 'Practical Performance Task'),
        ('PBL', 'Project-Based Learning'),
        ('OBS', 'Observation Rubric'),
        ('TEST', 'Written Test'),
    )

    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='tasks')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='assessment_tasks')
    title = models.CharField(max_length=160)
    task_type = models.CharField(max_length=10, choices=TASK_TYPE_CHOICES, default='PPT')
    strand = models.CharField(max_length=160, blank=True)
    sub_strand = models.CharField(max_length=160, blank=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_task_type_display()} - {self.title} - {self.learning_area}'


class AssessmentTaskResult(models.Model):
    """A single learner's recorded result against an AssessmentTask."""
    task = models.ForeignKey(AssessmentTask, on_delete=models.CASCADE, related_name='results')
    learner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='assessment_task_results')
    level_achieved = models.CharField(max_length=2, choices=CompetencyAssessment.LEVEL_CHOICES, default='ME')
    remark = models.TextField(blank=True)

    class Meta:
        unique_together = ['task', 'learner']

    def __str__(self):
        return f'{self.learner} - {self.task} - {self.get_level_achieved_display()}'


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
