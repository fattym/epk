from django.db import models

from accounts.models import User
from tenants.models import School


class Alumni(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='alumni')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alumni_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    graduation_year = models.PositiveSmallIntegerField()
    current_status = models.CharField(max_length=100, blank=True, help_text='e.g. University Student, Employed, Self-employed')
    current_institution = models.CharField(max_length=255, blank=True)
    current_employer = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_willing_to_be_mentored = models.BooleanField(default=False)
    is_willing_to_mentor = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-graduation_year', 'last_name']
        unique_together = ['school', 'email']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.graduation_year})'


class AlumniNetworkEvent(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='alumni_events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    alumni_attendees = models.ManyToManyField(Alumni, related_name='attended_events', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date']

    def __str__(self):
        return f'{self.title} - {self.event_date}'
