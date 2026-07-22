from django.db import models


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
        ('SICK_LEAVE', 'Sick Leave'),
        ('AUTHORIZED_ABSENCE', 'Authorized Absence'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='attendance_records')
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    note = models.TextField(blank=True, help_text='Absence reason, late excuse, or doctor note reference')
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recorded_attendances')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='attendance_records')

    class Meta:
        ordering = ['-date', 'student']
        unique_together = ['student', 'stream', 'date']

    def __str__(self):
        return f'{self.student} - {self.stream} - {self.date} - {self.status}'


class AttendanceSummary(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='attendance_summaries')
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='attendance_summaries')
    month = models.IntegerField()
    year = models.IntegerField()
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    late_days = models.IntegerField(default=0)
    excused_days = models.IntegerField(default=0)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='attendance_summaries')

    class Meta:
        ordering = ['-year', '-month', 'student']
        unique_together = ['student', 'stream', 'month', 'year']

    def __str__(self):
        return f'{self.student} - {self.stream} - {self.month}/{self.year}'


class AttendanceNotification(models.Model):
    TYPE_CHOICES = (
        ('ABSENT_ALERT', 'Absent Alert'),
        ('LOW_ATTENDANCE', 'Low Attendance Warning'),
        ('SICK_LEAVE', 'Sick Leave Notification'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='attendance_notifications')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='attendance_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    sent_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_notifications_received')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} - {self.notification_type} - {self.created_at.date()}'
