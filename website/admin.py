from django.contrib import admin
from .models import WebsiteConfig


@admin.register(WebsiteConfig)
class WebsiteConfigAdmin(admin.ModelAdmin):
    list_display = ['school', 'status', 'published_at', 'last_saved_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['school__name', 'school__code']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'last_saved_at']
    fieldsets = [
        ('School', {'fields': ['school', 'status']}),
        ('Branding', {'fields': [
            'primary_color', 'secondary_color', 'display_name', 'tagline',
            'homepage_title', 'homepage_subtitle', 'logo', 'hero_image',
        ]}),
        ('Content', {'fields': [
            'about_school', 'school_history', 'mission', 'headteacher_message',
            'admissions_info', 'contact_info', 'school_location',
        ]}),
        ('Sections & Featured', {'fields': [
            'sections', 'featured_notice_ids', 'featured_product_ids',
        ]}),
        ('Timestamps', {'fields': ['created_at', 'updated_at', 'published_at', 'last_saved_at']}),
    ]
