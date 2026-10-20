from django.db import models

from accounts.models import User
from tenants.models import School


class Supplier(models.Model):
    """Approved supplier / vendor for school procurement."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    kra_pin = models.CharField(max_length=50, blank=True, help_text='KRA PIN for Kenyan tax compliance')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['school', 'name']

    def __str__(self):
        return f'{self.name} ({self.school.name})'


class PurchaseOrder(models.Model):
    """A purchase request raised by staff, flowing through approval.

    Mirrors the brief's 'Procurement and Inventory' module: purchase requests,
    approval workflows, goods received, and asset tracking.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RECEIVED', 'Goods Received'),
        ('CANCELLED', 'Cancelled'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='purchase_orders',
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    purpose = models.TextField(help_text='What this order is for / justification')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    budget_code = models.CharField(max_length=100, blank=True, help_text='Ledger / budget heading')
    # Multi-level approval: each step records who approved and when.
    approval_chain = models.JSONField(default=list, help_text='[{"step": 1, "role": "ADMIN", "user_id": null, "approved_at": null}]')
    approved_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'PO #{self.id} - {self.supplier.name} ({self.status})'


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='items',
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # Link to a curriculum/material reference for traceability
    linked_learning_area = models.ForeignKey(
        'academics.LearningArea', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='purchase_order_items',
    )

    class Meta:
        ordering = ['id']

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f'{self.quantity} x {self.description} @ {self.unit_price}'


class GoodsReceived(models.Model):
    """Record of goods received against a PurchaseOrder (GRN)."""
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='goods_received',
    )
    received_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='received_items',
    )
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    condition_note = models.TextField(blank=True, help_text='Condition of goods on arrival')
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f'GRN #{self.id} - PO #{self.purchase_order.id}'


class StockItem(models.Model):
    """Inventory stock level for a catalogue item within a school."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='stock_items')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='piece')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        unique_together = ['school', 'name']

    @property
    def is_below_reorder(self):
        return self.quantity_in_stock <= self.reorder_level

    def __str__(self):
        return f'{self.name} ({self.quantity_in_stock} {self.unit})'


class Asset(models.Model):
    """Tracked school asset with depreciation info (brief: asset tracking)."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='assets')
    tag = models.CharField(max_length=100, help_text='Unique asset tag', unique=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assets',
    )
    serial_number = models.CharField(max_length=100, blank=True)
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()
    depreciation_years = models.PositiveSmallIntegerField(default=3)
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_assets',
    )
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=(
        ('IN_USE', 'In Use'),
        ('IN_REPAIR', 'In Repair'),
        ('SURPLUS', 'Surplus'),
        ('DISPOSED', 'Disposed'),
    ), default='IN_USE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date', 'name']

    def save(self, *args, **kwargs):
        if not self.tag:
            import datetime
            self.tag = f'AST-{self.school.id}-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        super().save(*args, **kwargs)

    @property
    def current_value(self):
        import datetime
        years_passed = (datetime.date.today() - self.purchase_date).days / 365.25
        if years_passed >= self.depreciation_years:
            return 0
        rate = 1 - years_passed / self.depreciation_years
        return round(self.purchase_cost * rate, 2)

    def __str__(self):
        return f'{self.tag} - {self.name}'
