from django.db import models


class Homework(models.Model):
    """A task assigned by a teacher to a stream (class) for a learning area (subject)."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='homeworks')
    learning_area = models.ForeignKey(
        'academics.LearningArea', on_delete=models.CASCADE, related_name='homeworks'
    )
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='homeworks')
    due_date = models.DateField()
    file = models.URLField(blank=True, help_text='Optional attachment URL (PDF/link)')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='homeworks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f'{self.title} · {self.stream}'


class HomeworkSubmission(models.Model):
    """A student's submission (or placeholder) for a given homework."""

    STATUS_CHOICES = (
        ('Not Submitted', 'Not Submitted'),
        ('Submitted', 'Submitted'),
        ('Late', 'Late'),
    )

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='homework_submissions')
    file_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Not Submitted')
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='homework_submissions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['student__first_name', 'student__last_name']
        unique_together = ['homework', 'student']

    def __str__(self):
        return f'{self.student} → {self.homework}'
