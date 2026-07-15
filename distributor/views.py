from django.db.models import Q
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from shop.views import sync_distributor_categories
from .models import DistributorProfile, DistributorProduct, SchoolOrder, SchoolOrderItem, Delivery
from .serializers import DistributorProfileSerializer, DistributorProductSerializer, SchoolOrderSerializer, DeliverySerializer

User = get_user_model()


class DistributorProfileViewSet(viewsets.ModelViewSet):
    queryset = DistributorProfile.objects.none()
    serializer_class = DistributorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'DISTRIBUTOR':
            return DistributorProfile.objects.filter(user=user)
        return DistributorProfile.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
        if user.role != 'DISTRIBUTOR':
            raise PermissionDenied('Only distributors can create products.')
        profile = user.distributor_profile
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
