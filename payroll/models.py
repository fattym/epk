from django.db import models

from accounts.models import User
from tenants.models import School


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='staff_profiles')
    employee_id = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    bank_account = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=50, blank=True)
    bank_branch = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-hire_date', 'employee_id']

    def __str__(self):
        return f'{self.user.email} - {self.designation}'


class LeaveType(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='leave_types')
    name = models.CharField(max_length=50)
    default_days_per_year = models.PositiveSmallIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.school.name})'


class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.PositiveSmallIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.staff} - {self.leave_type.name} ({self.status})'


class Payslip(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='payslips')
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['staff', 'month', 'year']

    def __str__(self):
        return f'{self.staff} - {self.month}/{self.year} - KES {self.net_salary}'


class PayrollSettings(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='payroll_settings')
    pay_period = models.CharField(max_length=20, choices=(
        ('MONTHLY', 'Monthly'),
        ('BIWEEKLY', 'Bi-weekly'),
        ('WEEKLY', 'Weekly'),
    ), default='MONTHLY')
    payable_days = models.PositiveSmallIntegerField(default=30)
    default_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
