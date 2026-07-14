from django.db import models
from accounts.models import User
from academics.models import LearningOutcome, Term


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
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at', 'learner', 'outcome']
        unique_together = ['learner', 'outcome', 'term']

    def __str__(self):
        return f'{self.learner} - {self.outcome} - {self.get_level_achieved_display()}'


class LearnerPortfolio(models.Model):
    learner = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='portfolio')
    current_level = models.CharField(max_length=2, choices=CompetencyAssessment.LEVEL_CHOICES, blank=True)
    strengths = models.TextField(blank=True)
    areas_for_growth = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Portfolio - {self.learner}'
