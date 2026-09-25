from rest_framework import serializers
from .models import (
    DistributorProfile, DistributorProduct, SchoolOrder, SchoolOrderItem, Delivery,
    DistributorWallet, WalletTransaction,
)


class DistributorProfileSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()

    class Meta:
        model = DistributorProfile
        fields = ['id', 'user', 'company_name', 'registration_number', 'address', 'phone', 'email', 'logo', 'is_verified', 'is_suspended', 'created_at', 'updated_at', 'wallet_balance']
        read_only_fields = ['id', 'user', 'is_verified', 'is_suspended', 'created_at', 'updated_at', 'wallet_balance']

    def get_wallet_balance(self, obj):
        try:
            return str(obj.wallet.balance)
        except DistributorWallet.DoesNotExist:
            return '0.00'


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


class WalletTransactionSerializer(serializers.ModelSerializer):
    order_total = serializers.DecimalField(source='order.total_amount', max_digits=10, decimal_places=2, read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)

    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet', 'order', 'order_total', 'order_status', 'amount', 'transaction_type', 'reference', 'created_at']
        read_only_fields = ['id', 'created_at']


class DistributorWalletSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.company_name', read_only=True)
    transactions = WalletTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = DistributorWallet
        fields = ['id', 'distributor', 'distributor_name', 'balance', 'total_earned',
                  'total_withdrawn', 'created_at', 'updated_at', 'transactions']
        read_only_fields = ['id', 'distributor', 'distributor_name', 'balance',
                            'total_earned', 'total_withdrawn', 'created_at', 'updated_at', 'transactions']
