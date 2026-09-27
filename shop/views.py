from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import csv
import re
from io import StringIO, BytesIO
from openpyxl import load_workbook
from academics.models import Grade, LearningArea
from .models import ProductCategory, Product, ProductVariant, ProductImage, Tag, Order, OrderItem, Payment, FormSubmission
from .serializers import (
    ProductCategorySerializer, ProductSerializer, ProductVariantSerializer,
    ProductImageSerializer, TagSerializer,
    OrderSerializer, OrderCreateSerializer, GuestOrderCreateSerializer,
    OrderItemSerializer, PaymentSerializer, FormSubmissionSerializer,
)
from accounts.permissions import IsAdminOrReadOnly
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
        user = self.request.user
        if user.is_superuser:
            return ProductCategory.objects.all()
        return ProductCategory.objects.filter(school=user.school)

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
        user = self.request.user
        if user.is_superuser:
            return Product.objects.all()
        return Product.objects.filter(school=user.school)

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

    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        product = self.get_object()
        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if not product.image and files:
            product.image = files[0]
            product.save()
        primary_exists = product.images.filter(is_primary=True).exists()
        order = product.images.count()
        for index, f in enumerate(files):
            ProductImage.objects.create(
                product=product,
                image=f,
                is_primary=not primary_exists and index == 0,
                order=order + index,
            )
        serializer = ProductImageSerializer(product.images.all(), many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def import_products(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'detail': 'Staff permission required.'}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        rows, error = self._rows_from_file(file)
        if rows is None:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        grades = list(Grade.objects.all())
        grade_by_name = {g.name.lower(): g for g in grades}
        stage_labels = {
            'pre_primary': ['pre-primary', 'kindergarten', 'pre primary'],
            'primary': ['primary school', 'primary'],
            'junior_secondary': ['junior secondary school', 'jss', 'junior secondary'],
            'senior_secondary': ['senior secondary school', 'sss', 'senior secondary'],
        }
        stage_lookup = {label: stage for stage, labels in stage_labels.items() for label in labels}
        for g in grades:
            for label in stage_labels.get(g.stage, []):
                stage_lookup[label] = g.stage
            stage_lookup[g.stage] = g.stage

        categories = list(ProductCategory.objects.all())
        cat_by_name = {c.name.lower(): c for c in categories}
        areas = list(LearningArea.objects.filter(school=request.user.school))
        area_by_name = {la.name.lower(): la for la in areas}

        created = 0
        failed = 0
        errors = []
        for row in rows:
            ok, data_or_err = self._build_product_data(
                row, grades, grade_by_name, stage_lookup, cat_by_name, area_by_name
            )
            if not ok:
                failed += 1
                errors.append({**{'name': (row.get('name') or '').strip()}, **data_or_err})
                continue
            serializer = self.get_serializer(data=data_or_err, context={'request': request})
            if serializer.is_valid():
                serializer.save(school=request.user.school)
                created += 1
            else:
                failed += 1
                errors.append({'name': (row.get('name') or '').strip(), 'errors': serializer.errors})
        return Response({'created': created, 'failed': failed, 'errors': errors}, status=status.HTTP_201_CREATED)

    def _rows_from_file(self, file):
        name = (file.name or '').lower()
        try:
            if name.endswith('.csv'):
                text = file.read().decode('utf-8-sig')
                reader = csv.DictReader(StringIO(text))
                return list(reader), None
            if name.endswith(('.xlsx', '.xls')):
                wb = load_workbook(BytesIO(file.read()), read_only=True)
                ws = wb.active
                rows = []
                for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                    if r_idx == 0:
                        headers = [self._cell_str(h) for h in row]
                        continue
                    rows.append(dict(zip(headers, [self._cell_str(v) for v in row])))
                return rows, None
            return None, 'Unsupported file type. Use .csv or .xlsx.'
        except Exception as exc:
            return None, f'Failed to parse file: {exc}'

    @staticmethod
    def _cell_str(value):
        if value is None:
            return ''
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    def _build_product_data(self, row, grades, grade_by_name, stage_lookup, cat_by_name, area_by_name):
        def col(*keys):
            for k in keys:
                if k in row and row[k] not in (None, ''):
                    return row[k]
            return ''

        name = (col('name') or '').strip()
        if not name:
            return False, {'skip': 'missing name'}
        category_name = (col('category', 'category_name', 'product_category') or '').strip()
        category = cat_by_name.get(category_name.lower())
        if not category and category_name:
            leaf = category_name.split('>')[-1].strip().lower()
            category = cat_by_name.get(leaf)
        category_id = category.id if category else None

        tokens = lambda key: [t.strip() for t in re.split(r'[;,]', col(key) or '') if t.strip()]
        institution_categories = tokens('institution_categories') or tokens('category_of_institution') or tokens('institution_category')
        institutions = [t for t in institution_categories if t]

        grade_ids = []
        for token in tokens('grade_levels') or tokens('grades') or tokens('applicable_levels'):
            low = token.lower()
            if low in stage_lookup:
                stage = stage_lookup[low]
                grade_ids += [g.id for g in grades if g.stage == stage]
            else:
                g = grade_by_name.get(low)
                if g:
                    grade_ids.append(g.id)
                else:
                    for cand in grade_by_name.values():
                        if low in cand.name.lower():
                            grade_ids.append(cand.id)
        grade_ids = list(dict.fromkeys(grade_ids))

        la_ids = []
        for token in tokens('learning_areas') or tokens('subjects') or tokens('learning_area'):
            la = area_by_name.get(token.lower())
            if not la:
                for cand in area_by_name.values():
                    if token.lower() in cand.name.lower():
                        la = cand
                        break
            if la:
                la_ids.append(la.id)
        la_ids = list(dict.fromkeys(la_ids))

        tag_names = [t for t in tokens('tags') if t]

        variants = []
        raw_variants = col('variants')
        if raw_variants:
            for chunk in raw_variants.split(';'):
                parts = [p.strip() for p in chunk.split(',')]
                if len(parts) >= 4:
                    variants.append({
                        'label': parts[0] or 'Default',
                        'size': parts[1] or '',
                        'color': parts[2] or '',
                        'stock_quantity': int(float(parts[3])),
                    })
        else:
            stock = col('stock_quantity', 'stock')
            if stock:
                variants.append({'label': 'Default', 'size': '', 'color': '', 'stock_quantity': int(float(stock))})

        pub = (col('publish', 'status', 'published') or '').lower()
        is_active = pub in ('publish', 'published', 'true', 'yes', 'active', '1')

        pt_raw = (col('product_type', 'type') or 'physical').lower()
        product_type = pt_raw if pt_raw in ('physical', 'digital', 'service') else 'physical'

        data = {
            'name': name,
            'category': category_id,
            'price': col('price', 'selling_price', 'selling price', 'amount'),
            'description': col('description') or '',
            'is_active': is_active,
            'product_type': product_type,
            'sku': col('sku'),
            'brand': col('brand'),
            'cost_price': col('cost_price'),
            'low_stock_threshold': col('low_stock_threshold', 'low_stock') or 0,
            'backorders': str(col('backorders', 'allow_backorders')).lower() in ('true', 'yes', '1'),
            'shipping_weight': col('shipping_weight'),
            'shipping_length': col('shipping_length'),
            'shipping_width': col('shipping_width'),
            'shipping_height': col('shipping_height'),
            'applicable_levels': grade_ids,
            'learning_areas': la_ids,
            'tags_data': tag_names,
            'institution_categories': institutions,
            'variants_data': variants,
        }
        return True, data


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
        if user.is_superuser:
            return Order.objects.all()
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

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def release_funds(self, request, pk=None):
        from .signals import credit_distributor_wallet
        order = self.get_object()
        if getattr(order, 'fund_status', 'HELD') != 'HELD':
            return Response({'detail': 'Funds are not held for this order.'}, status=status.HTTP_400_BAD_REQUEST)
        if order.status != 'delivered':
            return Response({'detail': 'Delivery must be confirmed before funds can be released.'}, status=status.HTTP_400_BAD_REQUEST)
        if getattr(order, 'disputed', False):
            return Response({'detail': 'Order is disputed; resolve the dispute before releasing funds.'}, status=status.HTTP_400_BAD_REQUEST)
        amount = credit_distributor_wallet(order)
        order.fund_status = 'RELEASED'
        order.released_at = timezone.now()
        order.released_by = request.user
        order.save(update_fields=['fund_status', 'released_at', 'released_by'])
        return Response({'detail': 'Funds released to distributor', 'fund_status': 'RELEASED', 'amount': str(amount or 0), 'released_at': order.released_at})

    @action(detail=True, methods=['post'])
    def confirm_delivery(self, request, pk=None):
        order = self.get_object()
        if order.status not in ('paid', 'ready_for_pickup', 'picked_up'):
            return Response({'detail': 'Order must be paid (and picked up) before confirming delivery.'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'delivered'
        order.delivery_confirmed_at = timezone.now()
        order.save(update_fields=['status', 'delivery_confirmed_at'])
        return Response({'detail': 'Delivery confirmed', 'order_status': 'delivered', 'fund_status': order.fund_status or 'HELD'})

    @action(detail=True, methods=['post'])
    def dispute(self, request, pk=None):
        order = self.get_object()
        reason = (request.data.get('reason') or '')[:500]
        if not reason:
            return Response({'detail': 'A dispute reason is required.'}, status=status.HTTP_400_BAD_REQUEST)
        order.disputed = True
        order.dispute_reason = reason
        if 'image' in request.data:
            order.dispute_evidence = request.data.get('image')
        order.save(update_fields=['disputed', 'dispute_reason', 'dispute_evidence'])
        return Response({'detail': 'Order reported; funds remain held', 'disputed': True})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrReadOnly])
    def refund(self, request, pk=None):
        order = self.get_object()
        if getattr(order, 'fund_status', 'HELD') == 'RELEASED':
            return Response({'detail': 'Funds already released; process a refund through the distributor.'}, status=status.HTTP_400_BAD_REQUEST)
        order.fund_status = 'REFUNDED'
        order.status = 'cancelled'
        order.save(update_fields=['fund_status', 'status'])
        return Response({'detail': 'Order refunded; funds held and returned to the customer flow', 'fund_status': 'REFUNDED'})


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


class FormSubmissionViewSet(viewsets.ModelViewSet):
    """Public form submissions (contact, onboarding, etc.) with admin review.

    - Anonymous users can POST to create submissions.
    - Staff/admins can list, retrieve, and update status.
    """
    queryset = FormSubmission.objects.all()
    serializer_class = FormSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'ADMIN':
            return FormSubmission.objects.all()
        return FormSubmission.objects.none()

    @action(detail=True, methods=['post'], url_path='mark-reviewed')
    def mark_reviewed(self, request, pk=None):
        submission = self.get_object()
        submission.status = 'reviewed'
        submission.save()
        return Response({'detail': 'Marked as reviewed', 'status': submission.status})

    @action(detail=True, methods=['post'], url_path='mark-resolved')
    def mark_resolved(self, request, pk=None):
        submission = self.get_object()
        submission.status = 'resolved'
        submission.save()
        return Response({'detail': 'Marked as resolved', 'status': submission.status})
