from django.db import models

from accounts.models import User
from tenants.models import School


class DisciplinaryRecord(models.Model):
    INCIDENT_TYPE_CHOICES = (
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
        ('DISRUPTION', 'Classroom Disruption'),
        ('BULLYING', 'Bullying'),
        ('DAMAGE', 'Property Damage'),
        ('CHEATING', 'Academic Dishonesty'),
        ('OTHER', 'Other'),
    )
    SEVERITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='disciplinary_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disciplinary_records')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES)
    description = models.TextField()
    action_taken = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='LOW')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_discipline')
    parent_notified = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.email} - {self.get_incident_type_display()} ({self.severity})'


class DisciplinaryAppeal(models.Model):
    record = models.ForeignKey(DisciplinaryRecord, on_delete=models.CASCADE, related_name='appeals')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appeals')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=(
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ), default='PENDING')
    decided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_appeals')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
