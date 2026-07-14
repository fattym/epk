from django.db import models


class Club(models.Model):
    """An extracurricular club (sports, drama, coding, etc.) run by one or more trainers."""
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='clubs')
    trainers = models.ManyToManyField('accounts.User', related_name='trained_clubs', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['school', 'name']

    def __str__(self):
        return self.name


class ClubSession(models.Model):
    """A daily log of what a trainer taught in a club session."""
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='sessions')
    trainer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='club_sessions')
    date = models.DateField()
    topic = models.CharField(max_length=255, help_text="What was taught in this session")
    notes = models.TextField(blank=True)
    attendees = models.ManyToManyField(
        'accounts.User', related_name='attended_club_sessions', blank=True
    )
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='club_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'club__name']

    def __str__(self):
        return f'{self.club} - {self.trainer} - {self.date}'
