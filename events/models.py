from django.db import models


class Event(models.Model):
    """A school event: academic, sports, cultural, holiday or exam."""

    TYPE_CHOICES = (
        ('Academic', 'Academic'),
        ('Sports', 'Sports'),
        ('Cultural', 'Cultural'),
        ('Holiday', 'Holiday'),
        ('Exam', 'Exam'),
        ('Other', 'Other'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Other')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    is_holiday = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.name
