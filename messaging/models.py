from django.db import models
from tenants.models import School
from accounts.models import User


class Announcement(models.Model):
    TARGET_AUDIENCE_CHOICES = [
        ('ALL', 'All'),
        ('TEACHERS', 'Teachers'),
        ('STUDENTS', 'Students'),
        ('PARENTS', 'Parents'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='ALL',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='announcements',
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    featured_products = models.ManyToManyField('shop.Product', blank=True, related_name='featured_in_announcements')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DirectMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
    )
    subject = models.CharField(max_length=255)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='direct_messages')

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return self.subject


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
