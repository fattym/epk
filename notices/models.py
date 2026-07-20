from django.db import models


class Notice(models.Model):
    """A school notice / announcement with flexible targeting and read tracking."""

    TARGET_CHOICES = (
        ('ALL', 'All'),
        ('TEACHERS', 'Teachers'),
        ('STUDENTS', 'Students'),
        ('PARENTS', 'Parents'),
        ('STREAM', 'Specific Class'),
        ('INDIVIDUAL', 'Individual'),
    )

    title = models.CharField(max_length=255)
    content = models.TextField()
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='ALL')
    target_stream = models.ForeignKey(
        'academics.Stream', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notices',
    )
    target_users = models.ManyToManyField(
        'accounts.User', blank=True, related_name='targeted_notices',
    )
    is_pinned = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_notices',
    )
    read_by = models.ManyToManyField(
        'accounts.User', blank=True, related_name='read_notices',
    )
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='notices')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
