from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ProductCategory, Product, ProductVariant, Order, OrderItem, Payment
from .serializers import ProductCategorySerializer, ProductSerializer, ProductVariantSerializer, OrderSerializer, OrderItemSerializer
from fees.models import Invoice
import uuid


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductCategory.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'is_active', 'applicable_levels']

    def get_queryset(self):
        return Product.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductVariant.objects.filter(product__school=self.request.user.school)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PARENT':
            return Order.objects.filter(parent=user)
        return Order.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user, school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = Order.objects.filter(parent=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pay_mpesa(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending_payment':
            return Response({'detail': 'Order is not pending payment'}, status=status.HTTP_400_BAD_REQUEST)

        phone = request.data.get('phone')
        if not phone:
            return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .services.mpesa import MpesaDaraja
        mpesa = MpesaDaraja()
        formatted_phone = mpesa.format_phone_number(phone)
        
        result = mpesa.initiate_stk_push(
            phone_number=formatted_phone,
            amount=order.total_amount,
            account_reference=f'ORDER-{order.id}',
            transaction_desc=f'Shop Order #{order.id}',
        )

        if result.get('success'):
            Payment.objects.create(
                order=order,
                method='mpesa',
                amount=order.total_amount,
                mpesa_checkout_request_id=result.get('checkout_request_id', ''),
                mpesa_phone_number=formatted_phone,
                status='initiated',
            )
            return Response({'detail': 'STK Push initiated. Please check your phone.', 'checkout_request_id': result.get('checkout_request_id')})
        else:
            return Response({'detail': result.get('error', 'Failed to initiate payment')}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pay_fee_balance(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending_payment':
            return Response({'detail': 'Order is not pending payment'}, status=status.HTTP_400_BAD_REQUEST)

        from fees.models import Invoice, FeeLedgerEntry
        from academics.models import Term

        current_term = Term.objects.filter(school=order.school, is_current=True).first()
        if not current_term:
            return Response({'detail': 'No active term found'}, status=status.HTTP_400_BAD_REQUEST)

        invoice, created = Invoice.objects.get_or_create(
            student=order.learner,
            defaults={
                'fee_structure': None,
                'amount': order.total_amount,
                'due_date': timezone.now().date(),
                'status': 'PENDING',
                'school': order.school,
            }
        )
        if not created:
            invoice.amount = (invoice.amount or 0) + order.total_amount
            invoice.save()

        order.status = 'paid'
        order.save()

        Payment.objects.create(
            order=order,
            method='fee_balance',
            amount=order.total_amount,
            status='confirmed',
        )

        return Response({'detail': 'Order added to fee balance', 'invoice_id': invoice.id})

    @action(detail=True, methods=['post'])
    def mark_ready(self, request, pk=None):
        order = self.get_object()
        if order.status != 'paid':
            return Response({'detail': 'Order must be paid first'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'ready_for_pickup'
        order.pickup_code = uuid.uuid4().hex[:8].upper()
        order.save()
        return Response({'detail': 'Order marked ready for pickup', 'pickup_code': order.pickup_code})

    @action(detail=True, methods=['post'])
    def mark_picked_up(self, request, pk=None):
        order = self.get_object()
        if order.status != 'ready_for_pickup':
            return Response({'detail': 'Order must be ready for pickup'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'picked_up'
        order.picked_up_at = timezone.now()
        order.picked_up_by_staff = request.user
        order.save()
        return Response({'detail': 'Order marked as picked up'})
