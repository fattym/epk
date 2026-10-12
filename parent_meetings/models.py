from django.db import models

from accounts.models import User
from tenants.models import School


class ParentTeacherMeeting(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='ptmeetings')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_meetings')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings_as_parent')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings_as_student')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=30)
    location = models.CharField(max_length=255, blank=True, help_text='Room or virtual link')
    agenda = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']
        unique_together = ['teacher', 'parent', 'student', 'scheduled_at']

    def __str__(self):
        return f'PTM: {self.teacher.email} ↔ {self.parent.email} for {self.student.email}'


class MeetingNote(models.Model):
    meeting = models.ForeignKey(ParentTeacherMeeting, on_delete=models.CASCADE, related_name='meeting_notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ptm_notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
