from django.db import models


class Complaint(models.Model):
    """A grievance raised by a student, parent or teacher and tracked by the school."""

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )

    CATEGORY_CHOICES = (
        ('Academic', 'Academic'),
        ('Disciplinary', 'Disciplinary'),
        ('Facilities', 'Facilities'),
        ('Fee', 'Fee'),
        ('Other', 'Other'),
    )

    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    submitted_by = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='submitted_complaints'
    )
    assigned_to = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        related_name='assigned_complaints', null=True, blank=True
    )
    resolution = models.TextField(blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='complaints')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ComplaintComment(models.Model):
    """A comment / progress note on a complaint (teacher reply, admin note, etc.)."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='complaint_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment on complaint #{self.complaint_id}'
