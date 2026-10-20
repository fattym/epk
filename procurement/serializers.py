from rest_framework import serializers

from .models import Asset, GoodsReceived, PurchaseOrder, PurchaseOrderItem, StockItem, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']

    def validate_name(self, value):
        request = self.context.get('request')
        school = getattr(getattr(request, 'user', None), 'school', None)
        if not school:
            raise serializers.ValidationError('School context is required.')
        qs = Supplier.objects.filter(school=school, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A supplier with this name already exists for the school.')
        return value


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'purchase_order', 'description', 'quantity', 'unit_price', 'line_total', 'linked_learning_area']
        read_only_fields = ['id', 'purchase_order']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'school', 'supplier', 'supplier_name', 'purpose', 'total_amount',
            'status', 'budget_code', 'approval_chain', 'approved_at', 'received_at',
            'requested_by', 'requested_by_name', 'approved_by', 'approved_by_name',
            'created_at', 'updated_at', 'items',
        ]
        read_only_fields = ['id', 'school', 'requested_by', 'created_at', 'updated_at', 'total_amount']

    def get_requested_by_name(self, obj):
        return obj.requested_by.email if obj.requested_by else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.email if obj.approved_by else None

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')
        validated_data.setdefault('requested_by', request.user if request else None)
        validated_data['school'] = getattr(request.user, 'school', None) if request else None
        po = PurchaseOrder.objects.create(**validated_data)
        total = 0
        for item in items_data:
            i = PurchaseOrderItem.objects.create(purchase_order=po, **item)
            total += i.line_total
        po.total_amount = total
        po.save()
        return po

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        # Rebuild line items for simplicity (full replacement)
        instance.items.all().delete()
        total = 0
        for item in items_data:
            i = PurchaseOrderItem.objects.create(purchase_order=instance, **item)
            total += i.line_total
        instance.total_amount = total
        instance.save()
        return instance


class GoodsReceivedSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceived
        fields = '__all__'
        read_only_fields = ['id', 'received_by', 'received_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['received_by'] = getattr(request, 'user', None)
        return GoodsReceived.objects.create(**validated_data)


class StockItemSerializer(serializers.ModelSerializer):
    is_below_reorder = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockItem
        fields = '__all__'
        read_only_fields = ['id', 'school', 'last_updated']


class AssetSerializer(serializers.ModelSerializer):
    current_value = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ['id', 'school', 'tag', 'created_at', 'updated_at']
