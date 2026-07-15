from django.db import models
from accounts.models import User
from tenants.models import School


class DistributorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='distributor_profile')
    company_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='distributor/logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class DistributorProduct(models.Model):
    distributor = models.ForeignKey(DistributorProfile, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='distributor/products/', blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_quantity = models.PositiveIntegerField(default=1)
    available_stock = models.PositiveIntegerField(default=0)
    tags = models.JSONField(default=list, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    bulk_pricing = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.distributor.company_name} - {self.name}'


class SchoolOrder(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='school_orders')
    distributor = models.ForeignKey(DistributorProfile, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='school_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.school.name} - {self.distributor.company_name} - {self.status}'


class SchoolOrderItem(models.Model):
    order = models.ForeignKey(SchoolOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(DistributorProduct, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'


class Delivery(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    )
    order = models.OneToOneField(SchoolOrder, on_delete=models.CASCADE, related_name='delivery')
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Delivery for {self.order}'
