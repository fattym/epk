from rest_framework import serializers
from .models import DistributorProfile, DistributorProduct, SchoolOrder, SchoolOrderItem, Delivery


class DistributorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributorProfile
        fields = ['id', 'user', 'company_name', 'registration_number', 'address', 'phone', 'email', 'logo', 'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'is_verified', 'created_at', 'updated_at']


class DistributorProductSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.company_name', read_only=True)
    class Meta:
        model = DistributorProduct
        fields = ['id', 'distributor', 'distributor_name', 'name', 'description', 'category', 'image', 'unit_price', 'min_order_quantity', 'available_stock', 'tags', 'attributes', 'bulk_pricing', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'distributor', 'distributor_name', 'created_at', 'updated_at']


class SchoolOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolOrderItem
        fields = ['id', 'order', 'product', 'quantity', 'unit_price']
        read_only_fields = ['id', 'order']


class SchoolOrderSerializer(serializers.ModelSerializer):
    items = SchoolOrderItemSerializer(many=True)

    class Meta:
        model = SchoolOrder
        fields = ['id', 'school', 'distributor', 'status', 'total_amount', 'notes', 'created_by', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'school', 'total_amount', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        total = sum(item['unit_price'] * item['quantity'] for item in items_data)
        validated_data['total_amount'] = total
        order = SchoolOrder.objects.create(**validated_data)
        for item_data in items_data:
            SchoolOrderItem.objects.create(order=order, **item_data)
        return order


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'order', 'tracking_number', 'carrier', 'status', 'estimated_delivery', 'delivered_at', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order', 'created_at', 'updated_at']
