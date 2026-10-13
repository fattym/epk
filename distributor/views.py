from django.db.models import Q
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from shop.views import sync_distributor_categories
from .models import (
    DistributorProfile, DistributorProduct, SchoolOrder, SchoolOrderItem, Delivery,
    DistributorWallet, WalletTransaction,
)
from .serializers import (
    DistributorProfileSerializer, DistributorProductSerializer, SchoolOrderSerializer,
    DeliverySerializer, WalletTransactionSerializer, DistributorWalletSerializer,
)

User = get_user_model()


class DistributorProfileViewSet(viewsets.ModelViewSet):
    queryset = DistributorProfile.objects.all()
    serializer_class = DistributorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'ADMIN':
            return DistributorProfile.objects.all()
        if user.role == 'DISTRIBUTOR':
            return DistributorProfile.objects.filter(user=user)
        return DistributorProfile.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        profile = self.get_object()
        profile.is_verified = True
        profile.save()
        serializer = self.get_serializer(profile)
        return Response({'detail': 'Distributor approved.', 'is_verified': True, 'profile': serializer.data})

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        profile = self.get_object()
        profile.is_suspended = True
        profile.save()
        serializer = self.get_serializer(profile)
        return Response({'detail': 'Distributor suspended.', 'is_suspended': True, 'profile': serializer.data})

    @action(detail=True, methods=['post'], url_path='unsuspend')
    def unsuspend(self, request, pk=None):
        profile = self.get_object()
        profile.is_suspended = False
        profile.save()
        serializer = self.get_serializer(profile)
        return Response({'detail': 'Distributor unsuspended.', 'is_suspended': False, 'profile': serializer.data})

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        pending = DistributorProfile.objects.filter(is_verified=False, is_suspended=False)
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='suspended')
    def suspended(self, request):
        suspended = DistributorProfile.objects.filter(is_suspended=True)
        serializer = self.get_serializer(suspended, many=True)
        return Response(serializer.data)


class DistributorProductViewSet(viewsets.ModelViewSet):
    queryset = DistributorProduct.objects.none()
    serializer_class = DistributorProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['distributor', 'category', 'is_active']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            try:
                profile = user.distributor_profile
                return DistributorProduct.objects.filter(distributor=profile)
            except DistributorProfile.DoesNotExist:
                return DistributorProduct.objects.none()
        if user.school:
            sync_distributor_categories(user.school)
        queryset = DistributorProduct.objects.filter(distributor__is_verified=True, is_active=True)
        category = self.request.query_params.get('category')
        tags = self.request.query_params.get('tags')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if category:
            queryset = queryset.filter(category__iexact=category)
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag])
        if min_price:
            queryset = queryset.filter(unit_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(unit_price__lte=max_price)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            profile = user.distributor_profile
        elif user.is_staff or user.role == 'ADMIN':
            distributor_id = self.request.data.get('distributor')
            if distributor_id:
                profile = DistributorProfile.objects.get(id=distributor_id)
            else:
                raise PermissionDenied('Admin must specify a distributor.')
        else:
            raise PermissionDenied('Only distributors or admins can create products.')
        serializer.save(distributor=profile)


class SchoolOrderViewSet(viewsets.ModelViewSet):
    queryset = SchoolOrder.objects.none()
    serializer_class = SchoolOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'distributor']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            try:
                profile = user.distributor_profile
                return SchoolOrder.objects.filter(distributor=profile)
            except DistributorProfile.DoesNotExist:
                return SchoolOrder.objects.none()
        return SchoolOrder.objects.filter(school=user.school)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(school=user.school, created_by=user)


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.none()
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            try:
                profile = user.distributor_profile
                return Delivery.objects.filter(order__distributor=profile)
            except DistributorProfile.DoesNotExist:
                return Delivery.objects.none()
        return Delivery.objects.filter(order__school=user.school)


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Distributors can view their own commission balance + transaction history.

    Staff/admins can view any wallet. The actual money from parent orders is
    collected into the global "Coding Clubs Kenya" account via M-Pesa; this
    endpoint merely *reflects* the balance owed to the distributor who supplied
    the goods.
    """
    queryset = DistributorWallet.objects.all()
    serializer_class = DistributorWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            try:
                profile = user.distributor_profile
                return DistributorWallet.objects.filter(distributor=profile)
            except DistributorProfile.DoesNotExist:
                return DistributorWallet.objects.none()
        return DistributorWallet.objects.all()

    @action(detail=False, methods=['get'])
    def summary(self, request):
        qs = self.get_queryset()
        from django.db.models import Sum, DecimalField
        agg = qs.aggregate(
            total_balance=Sum('balance', output_field=DecimalField()),
            total_earned=Sum('total_earned', output_field=DecimalField()),
        )
        return Response({
            'total_balance': str(agg['total_balance'] or 0),
            'total_earned': str(agg['total_earned'] or 0),
            'wallets': list(qs.values('distributor__company_name', 'balance', 'total_earned', 'total_withdrawn')),
        })
