from django.db import models

from accounts.models import User
from tenants.models import School


class HealthRecord(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='health_records')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_records')
    allergies = models.TextField(blank=True, help_text='Structured or comma-separated list')
    medications = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['school', 'student']

    def __str__(self):
        return f'{self.student.email} - Health Record'


class NurseVisit(models.Model):
    SEVERITY_CHOICES = (
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('SERIOUS', 'Serious'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='nurse_visits')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nurse_visits')
    health_record = models.ForeignKey(HealthRecord, on_delete=models.CASCADE, related_name='visits', null=True, blank=True)
    reason = models.TextField()
    treatment = models.TextField(blank=True)
    medication_given = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MINOR')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_visits')
    parent_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.email} - {self.severity} visit'
