from django.contrib import admin
from .models import RequiredItem, RequiredItemOption


@admin.register(RequiredItem)
class RequiredItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'class_level', 'term', 'is_mandatory', 'allow_external_purchase', 'preferred_source', 'is_published', 'created_at']
    list_filter = ['school', 'class_level', 'term', 'is_mandatory', 'is_published', 'preferred_source']
    search_fields = ['name', 'description', 'school__name', 'class_level__name']
    date_hierarchy = 'created_at'


@admin.register(RequiredItemOption)
class RequiredItemOptionAdmin(admin.ModelAdmin):
    list_display = ['required_item', 'source_type', 'price', 'distributor', 'location', 'delivery_available', 'is_recommended']
    list_filter = ['source_type', 'delivery_available', 'is_recommended']
    search_fields = ['required_item__name', 'distributor__company_name', 'location']
