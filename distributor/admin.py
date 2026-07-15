from django.contrib import admin
from .models import DistributorProfile, DistributorProduct, SchoolOrder, SchoolOrderItem, Delivery


@admin.register(DistributorProfile)
class DistributorProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'phone', 'email', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['company_name', 'user__email', 'phone', 'email']


@admin.register(DistributorProduct)
class DistributorProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'distributor', 'category', 'unit_price', 'min_order_quantity', 'available_stock', 'is_active']
    list_filter = ['distributor', 'category', 'is_active']
    search_fields = ['name', 'description', 'distributor__company_name']


@admin.register(SchoolOrder)
class SchoolOrderAdmin(admin.ModelAdmin):
    list_display = ['school', 'distributor', 'status', 'total_amount', 'created_by', 'created_at']
    list_filter = ['status', 'school', 'distributor']
    search_fields = ['school__name', 'distributor__company_name', 'notes']
    date_hierarchy = 'created_at'


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'tracking_number', 'carrier', 'estimated_delivery', 'delivered_at']
    list_filter = ['status', 'carrier']
    search_fields = ['tracking_number', 'order__school__name', 'order__distributor__company_name']
