from django.db import models


class FeeStructure(models.Model):
    FREQUENCY_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('TERMLY', 'Termly'),
        ('YEARLY', 'Yearly'),
    )
    name = models.CharField(max_length=255)
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='fee_structures')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    due_date = models.DateField()
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='fee_structures')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='invoices')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='invoices')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.id} - {self.student.email}"


class Payment(models.Model):
    METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MPESA', 'M-Pesa'),
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='payments')

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment {self.id} - {self.invoice.id}"
