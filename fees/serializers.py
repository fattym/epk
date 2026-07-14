from rest_framework import serializers
from .models import FeeStructure, Invoice, Payment


class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = ['id', 'name', 'stream', 'amount', 'frequency', 'due_date', 'school']
        read_only_fields = ['id', 'school']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'student', 'fee_structure', 'amount', 'due_date', 'status', 'paid_at', 'school']
        read_only_fields = ['id', 'school']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'method', 'reference', 'paid_at', 'recorded_by', 'school']
        read_only_fields = ['id', 'paid_at', 'school']
