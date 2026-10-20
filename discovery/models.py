from django.db import models


class ShoppableVideo(models.Model):
    """Short product demonstration videos linked to a product.

    Distributors submit video links (or approved uploads); staff reviews
    and approves them before they appear on the public Discovery page.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(
        help_text="YouTube / Vimeo embed URL or self-hosted video URL.",
    )
    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='discovery_videos',
    )
    distributor = models.ForeignKey(
        'distributor.DistributorProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shoppable_videos',
    )
    thumbnail_url = models.URLField(blank=True)
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title

    @property
    def product_name(self):
        return self.product.name if self.product else '—'

    @property
    def distributor_name(self):
        return self.distributor.company_name if self.distributor else '—'


class InstitutionEnquiry(models.Model):
    """Bulk-order enquiries submitted by schools / colleges / institutions."""
    INSTITUTION_TYPE_CHOICES = (
        ('pre_primary', 'Pre-Primary'),
        ('primary', 'Primary School'),
        ('junior_secondary', 'Junior Secondary'),
        ('senior_secondary', 'Senior Secondary'),
        ('university', 'University'),
        ('tvet', 'TVET / Vocational'),
        ('other', 'Other'),
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    institution_name = models.CharField(max_length=255)
    institution_type = models.CharField(
        max_length=30,
        choices=INSTITUTION_TYPE_CHOICES,
        default='primary',
    )
    message = models.TextField(blank=True)
    product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of product IDs the institution is interested in.",
    )
    status = models.CharField(
        max_length=20,
        choices=(
            ('new', 'New'),
            ('reviewed', 'Reviewed'),
            ('resolved', 'Resolved'),
        ),
        default='new',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Enquiry from {self.institution_name} ({self.name})'
