from django.contrib import admin

from .models import Asset, GoodsReceived, PurchaseOrder, PurchaseOrderItem, StockItem, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_approved', 'school']
    list_filter = ['is_approved', 'school']
    search_fields = ['name', 'contact_person', 'email', 'phone']


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'school', 'status', 'total_amount', 'requested_by', 'created_at']
    list_filter = ['status', 'school', 'created_at']
    search_fields = ['supplier__name', 'purpose']
    date_hierarchy = 'created_at'
    inlines = [PurchaseOrderItemInline]


@admin.register(GoodsReceived)
class GoodsReceivedAdmin(admin.ModelAdmin):
    list_display = ['id', 'purchase_order', 'received_by', 'quantity_received', 'received_at']
    list_filter = ['received_at']
    date_hierarchy = 'received_at'


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'quantity_in_stock', 'reorder_level', 'unit', 'is_below_reorder', 'school']
    list_filter = ['category', 'school', 'unit']
    search_fields = ['name', 'category']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['tag', 'name', 'school', 'category', 'status', 'purchase_cost', 'assigned_to']
    list_filter = ['status', 'school', 'category']
    search_fields = ['tag', 'name', 'serial_number']
