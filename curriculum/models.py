from django.db import models
from accounts.models import User
from academics.models import LearningArea, Stream, Term, Strand, SubStrand


class ReferenceDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = (
        ('curriculum_design', 'KICD Curriculum Design'),
        ('sample_scheme', 'Sample Scheme of Work'),
    )
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='reference_docs')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='reference_documents/%Y/')
    source_note = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='uploaded_docs')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='reference_docs')

    class Meta:
        ordering = ['-uploaded_at', 'learning_area']

    def __str__(self):
        return self.title


class SchemeOfWork(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Auto-generated Draft'),
        ('in_progress', 'Being Edited'),
        ('finalized', 'Finalized'),
    )
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='schemes')
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='schemes')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='schemes')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='schemes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='schemes')

    class Meta:
        ordering = ['-created_at']
        unique_together = ['teacher', 'learning_area', 'term', 'stream']

    def __str__(self):
        return f'{self.teacher} - {self.learning_area} - {self.term} - {self.stream}'


class SchemeWeek(models.Model):
    scheme = models.ForeignKey(SchemeOfWork, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.PositiveSmallIntegerField()
    strand = models.ForeignKey(Strand, on_delete=models.CASCADE, related_name='scheme_weeks')
    sub_strand = models.ForeignKey(SubStrand, on_delete=models.CASCADE, related_name='scheme_weeks')
    specific_learning_outcomes = models.TextField()
    key_inquiry_question = models.TextField(blank=True)
    learning_experiences = models.TextField(blank=True)
    learning_resources = models.TextField(blank=True)
    assessment_method = models.TextField(blank=True)
    reflection = models.TextField(blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='scheme_weeks')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='scheme_weeks')

    class Meta:
        ordering = ['week_number']

    def __str__(self):
        return f'Week {self.week_number} - {self.sub_strand}'
