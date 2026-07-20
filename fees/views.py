from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from .models import FeeStructure, Invoice, Payment
from .serializers import FeeStructureSerializer, InvoiceSerializer, PaymentSerializer


class FeeStructureViewSet(viewsets.ModelViewSet):
    serializer_class = FeeStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FeeStructure.objects.none()

    def get_queryset(self):
        return FeeStructure.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Invoice.objects.none()

    def get_queryset(self):
        return Invoice.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def defaulters(self, request):
        today = timezone.now().date()
        invoices = self.get_queryset().filter(due_date__lt=today).exclude(status__in=['PAID', 'CANCELLED'])
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def report(self, request):
        qs = self.get_queryset()
        total_expected = qs.aggregate(Sum('amount'))['amount__sum'] or 0
        
        payments = Payment.objects.filter(invoice__in=qs)
        total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
        
        total_pending = qs.exclude(status__in=['PAID', 'CANCELLED']).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'total_expected': total_expected,
            'total_paid': total_paid,
            'total_pending': total_pending,
        })


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.none()

    def get_queryset(self):
        return Payment.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        payment = serializer.save(school=self.request.user.school, recorded_by=self.request.user)
        
        # Update Invoice Status
        invoice = payment.invoice
        total_paid = Payment.objects.filter(invoice=invoice).aggregate(Sum('amount'))['amount__sum'] or 0
        if total_paid >= invoice.amount:
            invoice.status = 'PAID'
            invoice.paid_at = timezone.now()
            invoice.save()

    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        payment = self.get_object()
        
        student_profile = None
        if hasattr(payment.invoice.student, 'student_profile'):
            student_profile = payment.invoice.student.student_profile
            
        data = {
            'receipt_no': f"REC-{payment.id:06d}",
            'date': payment.paid_at,
            'student_name': f"{payment.invoice.student.first_name} {payment.invoice.student.last_name}",
            'admission_number': student_profile.admission_number if student_profile else None,
            'amount': payment.amount,
            'method': payment.method,
            'reference': payment.reference,
            'invoice_no': payment.invoice.id,
            'fee_structure': payment.invoice.fee_structure.name,
            'recorded_by': f"{payment.recorded_by.first_name} {payment.recorded_by.last_name}" if payment.recorded_by else 'System',
        }
        return Response(data)
