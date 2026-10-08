from django.db import models
from accounts.models import User
from academics.models import Grade
from tenants.models import School
from distributor.models import DistributorProduct


class ProductCategory(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='product_categories')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    class Meta:
        ordering = ['name']
        unique_together = ['school', 'name', 'parent']

    def __str__(self):
        if self.parent:
            return f'{self.school.name} - {self.parent.name} > {self.name}'
        return f'{self.school.name} - {self.name}'


class Product(models.Model):
    MARKUP_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    PRODUCT_TYPE_CHOICES = (
        ('physical', 'Physical'),
        ('digital', 'Digital'),
        ('service', 'Service'),
    )
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='shop/products/%Y/', blank=True, null=True)
    applicable_levels = models.ManyToManyField(Grade, blank=True, related_name='products')
    is_active = models.BooleanField(default=True)
    linked_distributor_product = models.ForeignKey(DistributorProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name='school_listings')
    markup_type = models.CharField(max_length=20, choices=MARKUP_TYPE_CHOICES, null=True, blank=True)
    markup_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_reseller_listing = models.BooleanField(default=False)
    sku = models.CharField(max_length=60, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='physical', blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    low_stock_threshold = models.PositiveIntegerField(default=0)
    backorders = models.BooleanField(default=False)
    shipping_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    shipping_length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    shipping_width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    shipping_height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    tags = models.ManyToManyField('shop.Tag', blank=True, related_name='products')
    learning_areas = models.ManyToManyField('academics.LearningArea', blank=True, related_name='shop_products')
    institution_categories = models.JSONField(
        default=list, blank=True,
        help_text="e.g. ['Pre-Primary','Primary School','University','TVET / Vocational']",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.linked_distributor_product and self.markup_type and self.markup_value is not None:
            base_price = self.linked_distributor_product.unit_price
            if self.markup_type == 'percentage':
                self.price = base_price * (1 + self.markup_value / 100)
                self.commission_amount = self.price - base_price
            else:
                self.price = base_price + self.markup_value
                self.commission_amount = self.markup_value
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        return self.price


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    label = models.CharField(max_length=50)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['label']
        unique_together = ['product', 'label']

    def __str__(self):
        return f'{self.product} - {self.label}'

    @property
    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.price


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/products/gallery/%Y/')
    alt = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'Image for {self.product}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),
        ('paid', 'Paid'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    FUND_STATUS_CHOICES = (
        ('HELD', 'Held'),
        ('RELEASED', 'Released'),
        ('REFUNDED', 'Refunded'),
    )
    parent = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='parent_orders', null=True, blank=True, help_text='Null for guest (no-account) orders.')
    learner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='learner_orders', null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='orders')
    delivery_name = models.CharField(max_length=200, blank=True, help_text='Guest delivery contact name.')
    delivery_phone = models.CharField(max_length=20, blank=True, help_text='Guest delivery phone (also used for the M-Pesa STK push).')
    delivery_address = models.TextField(blank=True)
    delivery_county = models.CharField(max_length=100, blank=True)
    delivery_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    pickup_code = models.CharField(max_length=8, unique=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text='Total commission credited to distributor(s) when this order is paid.')
    created_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    picked_up_by_staff = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_processed')
    fund_status = models.CharField(max_length=10, choices=FUND_STATUS_CHOICES, default='HELD', help_text='Escrow state of the order funds. HELD until delivery is confirmed and an admin releases the funds to the distributor.')
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='released_orders')
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    disputed = models.BooleanField(default=False)
    dispute_reason = models.TextField(blank=True)
    dispute_evidence = models.ImageField(upload_to='disputes/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.id} - {self.learner} - {self.school}'

    def total_commission(self):
        """Sum of per-item commissions owed to linked distributors."""
        total = 0
        for item in self.items.select_related('variant__product__linked_distributor_product__distributor').all():
            product = item.variant.product
            if product.linked_distributor_product and product.commission_amount is not None:
                total += product.commission_amount * item.quantity
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.variant} x{self.quantity}'


class Payment(models.Model):
    METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('fee_balance', 'Added to Fee Balance'),
    )
    STATUS_CHOICES = (
        ('initiated', 'Initiated'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    mpesa_phone_number = models.CharField(max_length=15, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Payment for Order #{self.order.id} - {self.method}'


class FormSubmission(models.Model):
    """Generic form submissions from the storefront (contact, onboarding, etc.).

    Allows anonymous public submissions via the API; staff/admins can review
    and manage them through the Django admin or REST API.
    """
    FORM_TYPE_CHOICES = (
        ('contact', 'Contact'),
        ('onboarding', 'Distributor Onboarding'),
        ('find_school_list', 'Find My School List'),
        ('upload_list', 'Upload My School List'),
        ('track_order', 'Track Your Order'),
        ('lead', 'Homepage Lead'),
        ('demo', 'Demo Request'),
    )
    STATUS_CHOICES = (
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    )
    form_type = models.CharField(max_length=50, choices=FORM_TYPE_CHOICES)
    data = models.JSONField()
    file = models.FileField(upload_to='form_submissions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'FormSubmission #{self.id} - {self.get_form_type_display()}'
