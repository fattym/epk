from django.db import models
from tenants.models import School
from academics.models import Grade, Term


class RequiredItem(models.Model):
    SOURCE_CHOICES = (
        ('school', 'School'),
        ('distributor', 'Distributor'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='required_items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    class_level = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='required_items')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='required_items')
    is_mandatory = models.BooleanField(default=True)
    allow_external_purchase = models.BooleanField(default=True)
    preferred_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='school')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_level__order', 'name']
        unique_together = ['school', 'name', 'class_level', 'term']

    def __str__(self):
        return f'{self.class_level.name} - {self.name} ({self.term.name})'


class RequiredItemOption(models.Model):
    SOURCE_CHOICES = (
        ('school', 'School'),
        ('distributor', 'Distributor'),
    )

    required_item = models.ForeignKey(RequiredItem, on_delete=models.CASCADE, related_name='options')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    distributor = models.ForeignKey('distributor.DistributorProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='required_item_options')
    location = models.CharField(max_length=255, blank=True)
    delivery_available = models.BooleanField(default=False)
    linked_product = models.ForeignKey('shop.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='required_item_options')
    linked_distributor_product = models.ForeignKey('distributor.DistributorProduct', on_delete=models.SET_NULL, null=True, blank=True, related_name='required_item_options')
    is_recommended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source_type', 'price']

    def __str__(self):
        return f'{self.required_item.name} - {self.get_source_type_display()} - KES {self.price}'
