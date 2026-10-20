from django.contrib import admin

from .models import InstitutionEnquiry, ShoppableVideo


@admin.register(ShoppableVideo)
class ShoppableVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'distributor', 'is_approved', 'is_featured', 'created_at']
    list_filter = ['is_approved', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'product__name']
    raw_id_fields = ['product', 'distributor']
    actions = ['approve', 'feature']

    def approve(self, request, queryset):
        queryset.update(is_approved=True)
    approve.short_description = "Approve selected videos"

    def feature(self, request, queryset):
        queryset.update(is_featured=True, is_approved=True)
    feature.short_description = "Feature & approve selected videos"


@admin.register(InstitutionEnquiry)
class InstitutionEnquiryAdmin(admin.ModelAdmin):
    list_display = ['institution_name', 'name', 'email', 'institution_type', 'status', 'created_at']
    list_filter = ['institution_type', 'status', 'created_at']
    search_fields = ['name', 'email', 'institution_name', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at']
