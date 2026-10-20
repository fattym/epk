from django.db.models import Q
from rest_framework import generics, permissions, viewsets

from distributor.models import DistributorProfile
from shop.models import Product, ProductCategory

from .models import ShoppableVideo
from .serializers import (
    DiscoveryProductSerializer,
    InstitutionEnquirySerializer,
    PublicCategorySerializer,
    PublicDistributorSerializer,
    ShoppableVideoSerializer,
)


class DiscoveryProductsView(generics.ListAPIView):
    """Public product discovery feed with search and filtering.

    GET /api/discovery/
    Query params:
      search, category, institution_type, distributor, min_price,
      max_price, is_reseller_listing, limit
    """
    serializer_class = DiscoveryProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(
            is_active=True,
            linked_distributor_product__isnull=False,
            linked_distributor_product__is_active=True,
            linked_distributor_product__distributor__is_verified=True,
            linked_distributor_product__distributor__is_suspended=False,
        ).select_related(
            'category',
            'linked_distributor_product',
            'linked_distributor_product__distributor',
        ).prefetch_related(
            'variants',
            'tags',
        )

        search = self.request.query_params.get('search', '').strip()
        category = self.request.query_params.get('category')
        institution_type = self.request.query_params.get('institution_type')
        distributor = self.request.query_params.get('distributor')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        is_reseller = self.request.query_params.get('is_reseller_listing')

        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(linked_distributor_product__name__icontains=search)
            )

        if category:
            qs = qs.filter(
                Q(category__name__iexact=category)
                | Q(category__id=category)
            )

        if institution_type:
            qs = qs.extra(
                where=["CAST(institution_categories AS TEXT) LIKE %s"],
                params=[f'%"{institution_type}"%'],
            )

        if distributor:
            qs = qs.filter(
                Q(linked_distributor_product__distributor__company_name=distributor)
                | Q(distributor_id=distributor)
            )

        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        if is_reseller is not None:
            if is_reseller in ('true', '1'):
                qs = qs.filter(is_reseller_listing=True)
            elif is_reseller in ('false', '0'):
                qs = qs.filter(is_reseller_listing=False)

        return qs.distinct()


class ProductPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only public product catalog.

    GET /api/products/      - list / search / filter
    GET /api/products/:id/  - detail
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = DiscoveryProductSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'is_reseller_listing']
    search_fields = ['name', 'description']

    def get_queryset(self):
        qs = Product.objects.filter(
            is_active=True,
        ).select_related(
            'category',
            'linked_distributor_product',
            'linked_distributor_product__distributor',
        ).prefetch_related(
            'variants',
            'tags',
        )

        category = self.request.query_params.get('category')
        institution_type = self.request.query_params.get('institution_type')
        distributor = self.request.query_params.get('distributor')
        search = self.request.query_params.get('search', '').strip()
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
            )

        if category:
            qs = qs.filter(
                Q(category__name__iexact=category)
                | Q(category__id=category)
            )

        if institution_type:
            qs = qs.extra(
                where=["CAST(institution_categories AS TEXT) LIKE %s"],
                params=[f'%"{institution_type}"%'],
            )

        if distributor:
            qs = qs.filter(
                Q(linked_distributor_product__distributor_id=distributor)
            )

        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        return qs.distinct()


class ShoppableVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Approved shoppable videos, optionally filtered by product or distributor.

    GET /api/videos/
    """
    queryset = ShoppableVideo.objects.filter(
        is_approved=True,
    ).select_related(
        'product',
        'distributor',
    ).prefetch_related('product__variants')
    serializer_class = ShoppableVideoSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['product', 'distributor']


class PublicDistributorListView(generics.ListAPIView):
    """Approved distributors for the marketplace directory.

    GET /api/distributors/
    """
    serializer_class = PublicDistributorSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = DistributorProfile.objects.filter(
            is_verified=True,
            is_suspended=False,
        ).prefetch_related('products')
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(company_name__icontains=search)
                | Q(products__name__icontains=search)
            ).distinct()
        return qs


class PublicCategoryListView(generics.ListAPIView):
    """Top-level product categories for filter dropdowns.

    GET /api/categories/
    """
    serializer_class = PublicCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return ProductCategory.objects.filter(
            parent__isnull=True,
        ).prefetch_related('children')[:50]


class InstitutionEnquiryView(generics.CreateAPIView):
    """Submit a bulk-order enquiry from an institution.

    POST /api/institution-enquiries/
    """
    serializer_class = InstitutionEnquirySerializer
    permission_classes = [permissions.AllowAny]
