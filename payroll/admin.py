from django.contrib import admin

from .models import LeaveRequest, LeaveType, PayrollSettings, Payslip, StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'designation', 'department', 'school', 'is_active']
    list_filter = ['school', 'department', 'is_active']
    search_fields = ['employee_id', 'user__email']
    autocomplete_fields = ['user']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'default_days_per_year', 'is_paid']
    list_filter = ['school', 'is_paid']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['staff', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'start_date', 'leave_type']
    search_fields = ['staff__employee_id']


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['staff', 'month', 'year', 'net_salary', 'is_paid']
    list_filter = ['year', 'month', 'is_paid']
    search_fields = ['staff__employee_id']


@admin.register(PayrollSettings)
class PayrollSettingsAdmin(admin.ModelAdmin):
    list_display = ['school', 'pay_period']
