from rest_framework import serializers
from .models import ProductCategory, Product, ProductVariant, Order, OrderItem, Payment


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'label', 'stock_quantity', 'price_override', 'effective_price']
        read_only_fields = ['id', 'effective_price']


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    linked_distributor_product_name = serializers.CharField(source='linked_distributor_product.name', read_only=True)
    distributor_price = serializers.DecimalField(source='linked_distributor_product.unit_price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'school', 'category', 'name', 'description', 'price', 'effective_price', 'image', 'applicable_levels', 'is_active', 'created_at', 'variants', 'linked_distributor_product', 'linked_distributor_product_name', 'distributor_price', 'markup_type', 'markup_value', 'commission_amount', 'is_reseller_listing']
        read_only_fields = ['id', 'created_at', 'school', 'effective_price', 'linked_distributor_product_name', 'distributor_price', 'commission_amount']


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ['school']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['unit_price']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['confirmed_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'parent', 'learner', 'school', 'status', 'pickup_code', 'total_amount', 'created_at', 'picked_up_at', 'items', 'payment']
        read_only_fields = ['id', 'created_at', 'pickup_code', 'school']
