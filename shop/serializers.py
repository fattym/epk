from rest_framework import serializers
from .models import (
    ProductCategory, Product, ProductVariant, ProductImage, Tag,
    Order, OrderItem, Payment, FormSubmission,
)
from academics.models import LearningArea, Grade
from tenants.models import School
import uuid


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt', 'is_primary', 'order']
        read_only_fields = ['id', 'product']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        image = data.get('image')
        if image and request is not None:
            data['image_url'] = request.build_absolute_uri(image) if not image.startswith('http') else image
        return data


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'label', 'size', 'color', 'stock_quantity', 'price_override', 'effective_price']
        read_only_fields = ['id', 'product', 'effective_price']


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    linked_distributor_product_name = serializers.CharField(source='linked_distributor_product.name', read_only=True)
    distributor_price = serializers.DecimalField(source='linked_distributor_product.unit_price', max_digits=10, decimal_places=2, read_only=True)
    distributor_name = serializers.CharField(source='linked_distributor_product.distributor.company_name', read_only=True)
    applicable_levels = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Grade.objects.all(), required=False)
    learning_areas = serializers.PrimaryKeyRelatedField(many=True, queryset=LearningArea.objects.all(), required=False)
    variants_data = serializers.JSONField(write_only=True, required=False)
    tags_data = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'school', 'category', 'category_name', 'name', 'description', 'price',
            'effective_price', 'image', 'applicable_levels', 'is_active',
            'created_at', 'variants', 'images', 'tags', 'linked_distributor_product',
            'linked_distributor_product_name', 'distributor_name', 'distributor_price',
            'commission_amount', 'markup_type', 'markup_value', 'is_reseller_listing',
            'sku', 'brand', 'product_type', 'cost_price', 'low_stock_threshold',
  'backorders', 'shipping_weight', 'shipping_length', 'shipping_width',
  'shipping_height', 'learning_areas', 'institution_categories', 'variants_data', 'tags_data',
]
        read_only_fields = [
            'id', 'created_at', 'school', 'effective_price',
            'linked_distributor_product_name', 'distributor_price', 'distributor_name',
            'commission_amount', 'variants', 'images', 'tags',
        ]

    def _create_nested(self, product, variants_data, tags_data):
        if variants_data:
            for v in variants_data:
                ProductVariant.objects.create(product=product, **v)
        if tags_data:
            for name in tags_data:
                tag, _ = Tag.objects.get_or_create(name=name)
                product.tags.add(tag)
        return product

    def create(self, validated_data):
        variants_data = validated_data.pop('variants_data', None)
        tags_data = validated_data.pop('tags_data', None)
        product = super().create(validated_data)
        return self._create_nested(product, variants_data, tags_data)

    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants_data', None)
        tags_data = validated_data.pop('tags_data', None)
        product = super().update(instance, validated_data)
        return self._create_nested(product, variants_data, tags_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        image = data.get('image')
        if image and request is not None:
            data['image_url'] = request.build_absolute_uri(image) if not image.startswith('http') else image
        return data


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ['school']


class OrderItemSerializer(serializers.ModelSerializer):
    variant_label = serializers.CharField(source='variant.label', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'variant', 'variant_label', 'product_name', 'quantity', 'unit_price']
        read_only_fields = ['id', 'order', 'unit_price', 'variant_label', 'product_name']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Accepts either a `variant` (for sized items) or a `product` (the variant is
    resolved to the product's default variant at checkout)."""
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), required=False, allow_null=True)
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['variant', 'product', 'quantity']
        validators = []

    def validate(self, attrs):
        variant = attrs.get('variant')
        product = attrs.get('product')
        if not variant and not product:
            raise serializers.ValidationError('Either variant or product is required.')
        if product is not None and variant is not None and variant.product_id != product.id:
            raise serializers.ValidationError('The selected variant does not belong to the given product.')
        if not variant and product is not None:
            variant = product.variants.filter(label='Default').first()
            if variant is None:
                variant = product.variants.create(label='Default', stock_quantity=0)
        attrs['variant'] = variant
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['confirmed_at']


class FormSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSubmission
        fields = ['id', 'form_type', 'data', 'file', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
        extra_kwargs = {
            'file': {'required': False},
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    learner_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'parent', 'learner', 'learner_name', 'school', 'status', 'pickup_code', 'total_amount', 'commission_earned', 'created_at', 'picked_up_at', 'items', 'payment', 'delivery_name', 'delivery_phone', 'delivery_address', 'delivery_county', 'delivery_notes', 'fund_status', 'released_at', 'released_by', 'delivery_confirmed_at', 'disputed', 'dispute_reason', 'dispute_evidence']
        read_only_fields = ['id', 'created_at', 'pickup_code', 'school', 'commission_earned', 'fund_status', 'released_at', 'released_by', 'delivery_confirmed_at', 'disputed', 'dispute_reason']

    def get_learner_name(self, obj):
        if obj.learner_id:
            return f'{obj.learner.first_name} {obj.learner.last_name}'.strip() or obj.learner.email
        return None


class OrderCreateSerializer(serializers.ModelSerializer):
    """Used by parents to place a new shop order (checkout).

    Accepts a learner id and a list of {variant, quantity} items. The parent
    and school are derived from the authenticated request.
    """
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'parent', 'learner', 'school', 'status', 'total_amount',
                  'commission_earned', 'created_at', 'items']
        read_only_fields = ['id', 'parent', 'school', 'status', 'total_amount',
                            'commission_earned', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order(pickup_code=uuid.uuid4().hex[:8].upper(), **validated_data)
        total = 0
        order_items = []
        for item_data in items_data:
            variant = item_data['variant']
            quantity = item_data['quantity']
            unit_price = variant.effective_price
            total += unit_price * quantity
            order_items.append(OrderItem(
                variant=variant, quantity=quantity, unit_price=unit_price,
            ))
        order.total_amount = total
        order.save()
        for item in order_items:
            item.order = order
        OrderItem.objects.bulk_create(order_items)
        return order


class GuestOrderCreateSerializer(serializers.ModelSerializer):
    """Used by anonymous shoppers to place a no-account shop order.

    ``parent`` and ``learner`` are intentionally omitted — they are forced to
    ``None``. A ``school`` is resolved from the first ordered item's product
    (public storefront products always belong to the host school); if the cart
    is empty we fall back to the first school in the database.
    """
    items = OrderItemCreateSerializer(many=True)
    delivery_name = serializers.CharField()
    delivery_phone = serializers.CharField()
    delivery_address = serializers.CharField()
    delivery_county = serializers.CharField(required=False, allow_blank=True)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = [
            'id', 'parent', 'learner', 'school', 'status', 'total_amount',
            'commission_earned', 'created_at', 'items',
            'delivery_name', 'delivery_phone', 'delivery_address',
            'delivery_county', 'delivery_notes',
        ]
        read_only_fields = [
            'id', 'parent', 'learner', 'school', 'status', 'total_amount',
            'commission_earned', 'created_at',
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        delivery = {
            k: validated_data.pop(k, '')
            for k in ('delivery_name', 'delivery_phone', 'delivery_address',
                      'delivery_county', 'delivery_notes')
            if k in validated_data
        }
        order = Order(parent=None, learner=None, pickup_code=uuid.uuid4().hex[:8].upper(), **delivery)
        total = 0
        order_items = []
        for item_data in items_data:
            variant = item_data['variant']
            quantity = item_data['quantity']
            unit_price = variant.effective_price
            total += unit_price * quantity
            order_items.append(OrderItem(
                variant=variant, quantity=quantity, unit_price=unit_price,
            ))
        if order_items:
            order.school = order_items[0].variant.product.school
        else:
            order.school = School.objects.first()
        order.total_amount = total
        order.save()
        for item in order_items:
            item.order = order
        OrderItem.objects.bulk_create(order_items)
        return order
