from django.db import models


class AtRiskFlag(models.Model):
    """A flag raised by the periodic at-risk learner analysis.

    Flags are *advisory* — they notify teachers/admins so a human can
    intervene.  They never mutate a CompetencyAssessment or fee record
    (brief §4.5 — human-in-the-loop).
    """

    FLAG_TYPE_CHOICES = (
        ('attendance', 'Attendance Drop'),
        ('competency', 'Repeated Below/Accepting Expectation'),
        ('fees', 'Fee Arrears'),
        ('combined', 'Combined Risk'),
    )

    school = models.ForeignKey(
        'tenants.School', on_delete=models.CASCADE, related_name='at_risk_flags',
    )
    learner = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='at_risk_flags',
    )
    flag_type = models.CharField(max_length=20, choices=FLAG_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=(
        ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'),
    ), default='MEDIUM')
    reason = models.TextField(help_text='Plain-language summary of why the flag was raised.')
    details = models.JSONField(default=dict, help_text='Structured data backing the flag.')
    acknowledged_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='acknowledged_risk_flags',
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'resolved', 'created_at']),
            models.Index(fields=['learner', '-created_at']),
        ]

    def __str__(self):
        return f'{self.learner} - {self.flag_type} ({self.severity})'
