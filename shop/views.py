from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import ProductCategory, Product, ProductVariant, Order, OrderItem, Payment
from .serializers import (
    ProductCategorySerializer, ProductSerializer, ProductVariantSerializer,
    OrderSerializer, OrderCreateSerializer, GuestOrderCreateSerializer,
    OrderItemSerializer, PaymentSerializer,
)
from fees.models import Invoice
from distributor.models import DistributorProduct
import uuid
import logging

logger = logging.getLogger(__name__)


def sync_distributor_categories(school):
    categories = DistributorProduct.objects.filter(
        distributor__is_verified=True,
        is_active=True,
        category__isnull=False,
    ).exclude(category='').values_list('category', flat=True).distinct()
    created = 0
    for category_name in categories:
        obj, was_created = ProductCategory.objects.get_or_create(
            school=school,
            name=category_name,
            defaults={'name': category_name},
        )
        if was_created:
            created += 1
    return created


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductCategory.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['post'])
    def sync_from_distributors(self, request):
        created = sync_distributor_categories(request.user.school)
        return Response({'detail': f'Synced categories from distributors.', 'created': created})


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'is_active', 'applicable_levels', 'is_reseller_listing']

    def get_queryset(self):
        return Product.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['post'])
    def import_from_distributor(self, request):
        distributor_product_id = request.data.get('distributor_product_id')
        markup_type = request.data.get('markup_type', 'percentage')
        markup_value = request.data.get('markup_value')
        category_id = request.data.get('category_id')

        if not distributor_product_id or markup_value is None:
            return Response({'detail': 'distributor_product_id and markup_value are required.'}, status=status.HTTP_400_BAD_REQUEST)

        distributor_product = get_object_or_404(DistributorProduct, id=distributor_product_id, is_active=True, distributor__is_verified=True)

        category = None
        if category_id:
            from .models import ProductCategory
            category = get_object_or_404(ProductCategory, id=category_id, school=request.user.school)
        else:
            from .models import ProductCategory
            category, _ = ProductCategory.objects.get_or_create(
                school=request.user.school,
                name=distributor_product.category or 'Imported',
            )

        product = Product(
            school=request.user.school,
            category=category,
            name=distributor_product.name,
            description=distributor_product.description,
            linked_distributor_product=distributor_product,
            markup_type=markup_type,
            markup_value=markup_value,
            is_reseller_listing=True,
        )
        product.save()
        product.applicable_levels.set([])

        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProductVariant.objects.filter(product__school=self.request.user.school)


class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Anonymous storefront catalog: all active products available for resale.

    The parent does not need an account to *browse*. The actual money from a
    later purchase still lands in the global Coding Clubs Kenya account; the
    commission is only credited to a distributor once a (logged-in) parent pays.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related(
            'category', 'linked_distributor_product',
            'linked_distributor_product__distributor',
        ).prefetch_related('variants')
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

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

        phone = request.data.get('phone') or request.user.phone
        if not phone:
            return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .services.mpesa import ChamaGoIntegrator
        mpesa = ChamaGoIntegrator()
        formatted_phone = mpesa.format_phone_number(phone)

        user_name = getattr(request.user, 'first_name', '') or getattr(request.user, 'email', '') or f'User #{request.user.id}'
        wallet = mpesa.create_wallet(
            holder_name=user_name,
            name=f'{user_name} - Order #{order.id}',
        )
        wallet_id = wallet.get('account_number')

        result = mpesa.initiate_stk_push(
            phone_number=formatted_phone,
            amount=order.total_amount,
            wallet=wallet_id,
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
            return Response({'detail': 'STK Push initiated. Please check your phone.', 'checkout_request_id': result.get('checkout_request_id'), 'wallet': wallet_id})
        else:
            return Response({'detail': result.get('error', 'Failed to initiate payment')}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        """Mark a payment as confirmed (e.g. via M-Pesa callback) and credit
        the linked distributor wallet(s) with the recorded commission."""
        order = self.get_object()
        try:
            payment = order.payment
        except Payment.DoesNotExist:
            return Response({'detail': 'No payment exists for this order'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.status == 'confirmed':
            return Response({'detail': 'Payment already confirmed', 'order_status': order.status})

        payment.status = 'confirmed'
        payment.mpesa_receipt_number = request.data.get('mpesa_receipt_number', payment.mpesa_receipt_number) or ''
        payment.save()
        order.status = 'paid'
        order.save()
        from .signals import credit_for_payment
        credit_for_payment(payment)
        serializer = PaymentSerializer(payment)
        return Response({'detail': 'Payment confirmed', 'order_status': order.status, 'payment': serializer.data})

    @action(detail=True, methods=['post'])
    def pay_fee_balance(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending_payment':
            return Response({'detail': 'Order is not pending payment'}, status=status.HTTP_400_BAD_REQUEST)

        from fees.models import Invoice
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


class GuestOrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Anonymous storefront checkout.

    A shopper with no account can place an order, receive an M-Pesa STK push,
    and confirm the payment. ``parent``/``learner`` are stored as ``None`` and
    the delivery details supplied by the shopper are saved on the order.
    """
    queryset = Order.objects.all().prefetch_related('items', 'payment')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return GuestOrderCreateSerializer
        return OrderSerializer

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])

    @action(detail=True, methods=['post'], url_path='pay_mpesa')
    def pay_mpesa(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending_payment':
            return Response({'detail': 'Order is not pending payment'}, status=status.HTTP_400_BAD_REQUEST)

        phone = request.data.get('phone') or order.delivery_phone
        if not phone:
            return Response({'detail': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .services.mpesa import ChamaGoIntegrator
        mpesa = ChamaGoIntegrator()
        formatted_phone = mpesa.format_phone_number(phone)

        wallet = mpesa.create_wallet(
            holder_name=order.delivery_name or f'Order #{order.id}',
            name=f'{order.delivery_name or "Guest"} - Order #{order.id}',
        )
        wallet_id = wallet.get('account_number')

        result = mpesa.initiate_stk_push(
            phone_number=formatted_phone,
            amount=order.total_amount,
            wallet=wallet_id,
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
            return Response({
                'detail': 'STK Push initiated. Check your phone to complete the payment.',
                'checkout_request_id': result.get('checkout_request_id'),
                'amount': order.total_amount,
                'wallet': wallet_id,
            })
        return Response({'detail': result.get('error', 'Failed to initiate payment')}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        order = self.get_object()
        try:
            payment = order.payment
        except Payment.DoesNotExist:
            if request.data.get('force'):
                payment = Payment.objects.create(
                    order=order, method='mpesa',
                    amount=order.total_amount,
                    mpesa_phone_number=order.delivery_phone or '',
                    status='initiated',
                )
            else:
                return Response({'detail': 'No payment exists for this order'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.status == 'confirmed':
            return Response({'detail': 'Payment already confirmed', 'order_status': order.status})

        checkout_request_id = request.data.get('checkout_request_id') or ''
        if checkout_request_id and checkout_request_id != payment.mpesa_checkout_request_id:
            return Response({'detail': 'Checkout request id does not match'}, status=status.HTTP_400_BAD_REQUEST)
        if not checkout_request_id and not request.data.get('force'):
            return Response({'detail': 'checkout_request_id is required to confirm a guest payment'},
                            status=status.HTTP_400_BAD_REQUEST)

        payment.status = 'confirmed'
        payment.mpesa_receipt_number = request.data.get('mpesa_receipt_number', payment.mpesa_receipt_number) or ''
        payment.save()
        order.status = 'paid'
        order.save()
        from .signals import credit_for_payment
        credit_for_payment(payment)
        serializer = PaymentSerializer(payment)
        return Response({'detail': 'Payment confirmed', 'order_status': order.status, 'payment': serializer.data})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def chama_webhook(request):
    """Handle asynchronous ``deposit.received`` callbacks from ChamaGO Integrator.

    Payload:
        event, amount, mobile, account_number, transaction_code, transaction_id
    """
    event = request.data.get('event')
    if event != 'deposit.received':
        return Response({'detail': 'Ignored'}, status=status.HTTP_200_OK)

    transaction_id = request.data.get('transaction_id') or request.data.get('transaction_code')
    if not transaction_id:
        return Response({'detail': 'Missing transaction_id'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.get(mpesa_checkout_request_id=transaction_id)
    except Payment.DoesNotExist:
        logger.warning(f'Webhook: no payment found for transaction_id={transaction_id}')
        return Response({'detail': 'No matching payment'}, status=status.HTTP_404_NOT_FOUND)

    if payment.status == 'confirmed':
        return Response({'detail': 'Payment already confirmed'}, status=status.HTTP_200_OK)

    payment.status = 'confirmed'
    payment.mpesa_receipt_number = request.data.get('transaction_code', '') or ''
    payment.mpesa_phone_number = request.data.get('mobile', payment.mpesa_phone_number)
    payment.save()

    order = payment.order
    order.status = 'paid'
    order.save()

    from .signals import credit_for_payment
    credit_for_payment(payment)

    logger.info(f'Webhook: payment {payment.id} for order {order.id} confirmed via ChamaGO callback')
    return Response({'detail': 'Payment confirmed', 'order_status': order.status})
