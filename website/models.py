from django.db import models
from django.core.validators import FileExtensionValidator
from tenants.models import School


def validate_image_size(value):
    """Validate image file size does not exceed 5MB."""
    max_size = 5 * 1024 * 1024  # 5MB
    if value.size > max_size:
        raise models.ValidationError('Image file too large (max 5MB).')


IMAGE_VALIDATORS = [
    FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif']),
    validate_image_size,
]


class WebsiteConfig(models.Model):
    """Website configuration for a school's public website.

    One per school.  Holds branding, content, section visibility/order and the
    draft/publish lifecycle.  Draft changes never affect the live public site
    until explicitly published.
    """

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('unpublished', 'Unpublished'),
    )

    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE,
        related_name='website_config',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Draft = not visible publicly; Published = live; Unpublished = taken down.',
    )

    # ---- Branding ---------------------------------------------------------
    primary_color = models.CharField(max_length=7, default='#2563eb')
    secondary_color = models.CharField(max_length=7, default='#0ea5e9')
    display_name = models.CharField(max_length=255, blank=True,
                                    help_text='Override the school name shown on the website.')
    tagline = models.CharField(max_length=255, blank=True)
    homepage_title = models.CharField(max_length=255, blank=True)
    homepage_subtitle = models.TextField(blank=True)
    logo = models.ImageField(upload_to='websites/logos/', blank=True, null=True, validators=IMAGE_VALIDATORS)
    hero_image = models.ImageField(upload_to='websites/heroes/', blank=True, null=True, validators=IMAGE_VALIDATORS)

    # ---- Content ----------------------------------------------------------
    about_school = models.TextField(blank=True)
    school_history = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    headteacher_message = models.TextField(blank=True)
    admissions_info = models.TextField(blank=True)
    contact_info = models.TextField(blank=True)
    school_location = models.TextField(blank=True)

    # ---- Sections ---------------------------------------------------------
    # JSON: { "hero": {"visible": true, "order": 1}, "about": {...}, ... }
    sections = models.JSONField(default=dict, blank=True)

    # ---- Featured content (referenced by ID) ------------------------------
    featured_notice_ids = models.JSONField(default=list, blank=True)
    featured_product_ids = models.JSONField(default=list, blank=True)

    # ---- Lifecycle timestamps ---------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_saved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Website configuration'
        verbose_name_plural = 'Website configurations'

    def __str__(self):
        return f'Website config for {self.school.name} ({self.get_status_display()})'

    @property
    def is_public(self):
        return self.status == 'published'
