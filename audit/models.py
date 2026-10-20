from django.db import models


class AuditLog(models.Model):
    """Generic audit log for sensitive actions across the school ERP.

    Every entry captures *who* did *what* to *which object*, with optional
    before/after snapshots so changes can be diffed.  AI-generated suggestions
    are logged with ``action == 'ai_suggestion'`` and never conflated with
    human-confirmed writes (see AGENTS.md §4 implementation note).
    """

    ACTION_CHOICES = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('ai_suggestion', 'AI Suggestion (draft)'),
    )

    school = models.ForeignKey(
        'tenants.School', on_delete=models.CASCADE, related_name='audit_logs',
        null=True, blank=True, help_text='Null for cross-tenant system actions.',
    )
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    # Generic relation so a single table covers every auditable model.
    content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True,
    )
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    field = models.CharField(max_length=100, blank=True, help_text='Specific field that changed.')
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.action} {self.object_repr} by {self.user or "system"} at {self.created_at}'
