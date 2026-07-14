from django.contrib import admin
from .models import FeeStructure, Invoice, Payment


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream', 'amount', 'frequency', 'due_date', 'school']
    list_filter = ['frequency', 'school', 'due_date']
    search_fields = ['name']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'fee_structure', 'amount', 'due_date', 'status', 'paid_at', 'school']
    list_filter = ['status', 'school', 'due_date']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'amount', 'method', 'reference', 'paid_at', 'recorded_by', 'school']
    list_filter = ['method', 'school', 'paid_at']
    search_fields = ['reference']
