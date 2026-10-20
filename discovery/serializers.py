from rest_framework import serializers

from distributor.models import DistributorProfile
from shop.models import Product, ProductCategory, ProductVariant

from .models import InstitutionEnquiry, ShoppableVideo


class DiscoveryProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'label', 'size', 'color', 'stock_quantity', 'effective_price']

    def get_effective_price(self, obj):
        return str(obj.effective_price)


class DiscoveryProductSerializer(serializers.ModelSerializer):
    """Public-facing product serializer for the Discovery page.

    Exposes only safe, customer-facing fields. Never leaks cost_price,
    commission internals, or distributor payout details.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    effective_price = serializers.SerializerMethodField()
    distributor_name = serializers.CharField(
        source='linked_distributor_product.distributor.company_name',
        read_only=True,
    )
    distributor_id = serializers.IntegerField(
        source='linked_distributor_product.distributor.id',
        read_only=True,
    )
    total_stock = serializers.SerializerMethodField()
    variants = DiscoveryProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'effective_price',
            'image_url', 'category', 'category_name', 'is_active',
            'institution_categories', 'brand', 'product_type',
            'is_reseller_listing', 'commission_amount',
            'tags', 'learning_areas', 'created_at',
            'distributor_name', 'distributor_id',
            'total_stock', 'variants',
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_effective_price(self, obj):
        return str(obj.effective_price)

    def get_total_stock(self, obj):
        try:
            return sum(v.stock_quantity for v in obj.variants.all())
        except Exception:
            return 0


class ShoppableVideoSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    product_price = serializers.SerializerMethodField()
    product_image_url = serializers.SerializerMethodField()
    product_url = serializers.SerializerMethodField()

    class Meta:
        model = ShoppableVideo
        fields = [
            'id', 'title', 'description', 'video_url', 'thumbnail_url',
            'product', 'product_name', 'product_price', 'product_image_url',
            'product_url', 'distributor', 'is_approved', 'is_featured',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'product_name', 'product_price', 'product_image_url',
            'product_url', 'created_at', 'updated_at',
        ]

    def get_product_name(self, obj):
        return obj.product.name if obj.product else None

    def get_product_price(self, obj):
        if obj.product:
            return str(obj.product.effective_price)
        return None

    def get_product_image_url(self, obj):
        if obj.product and obj.product.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        return None

    def get_product_url(self, obj):
        if obj.product:
            return f'/products/{obj.product.id}/'
        return None


class PublicDistributorSerializer(serializers.ModelSerializer):
    """Approved distributor profile for the marketplace directory."""
    logo_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    distributor_products = serializers.SerializerMethodField()

    class Meta:
        model = DistributorProfile
        fields = [
            'id', 'company_name', 'registration_number', 'address',
            'phone', 'email', 'logo_url', 'is_verified',
            'product_count', 'distributor_products', 'created_at',
        ]
        read_only_fields = [
            'id', 'is_verified', 'product_count', 'distributor_products',
            'created_at',
        ]

    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def get_distributor_products(self, obj):
        products = obj.products.filter(is_active=True)[:6]
        return [
            {
                'id': p.id,
                'name': p.name,
                'unit_price': str(p.unit_price),
                'image_url': self.context['request'].build_absolute_uri(p.image.url) if p.image else None,
            }
            for p in products
        ]


class PublicCategorySerializer(serializers.ModelSerializer):
    """Public product categories for filter dropdowns."""
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent', 'children']
        read_only_fields = ['id', 'name', 'parent', 'children']

    def get_children(self, obj):
        return [
            {'id': c.id, 'name': c.name}
            for c in obj.children.all()[:10]
        ]


class InstitutionEnquirySerializer(serializers.ModelSerializer):
    """Bulk-order enquiry submitted by institutions."""
    class Meta:
        model = InstitutionEnquiry
        fields = [
            'id', 'name', 'email', 'phone', 'institution_name',
            'institution_type', 'message', 'product_ids',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at',
        ]
