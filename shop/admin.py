from django.contrib import admin
from .models import ProductCategory, Product, ProductVariant, Order, OrderItem, Payment


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'school']
    list_filter = ['school']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'school', 'is_active', 'created_at']
    list_filter = ['category', 'school', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['applicable_levels']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'label', 'stock_quantity', 'price_override']
    list_filter = ['product']
    search_fields = ['label', 'product__name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'parent', 'learner', 'school', 'status', 'total_amount', 'pickup_code', 'created_at']
    list_filter = ['status', 'school', 'created_at']
    search_fields = ['pickup_code', 'parent__email', 'learner__email']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'variant', 'quantity', 'unit_price']
    list_filter = ['order']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'amount', 'status', 'confirmed_at']
    list_filter = ['method', 'status']
    search_fields = ['order__id', 'mpesa_receipt_number']
