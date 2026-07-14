from django.db import models


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='attendance_records')
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
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
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='attendance_summaries')

    class Meta:
        ordering = ['-year', '-month', 'student']
        unique_together = ['student', 'stream', 'month', 'year']

    def __str__(self):
        return f'{self.student} - {self.stream} - {self.month}/{self.year}'
