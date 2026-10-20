from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'action', 'school', 'user', 'content_type', 'object_repr', 'object_id']
    list_filter = ['action', 'school', 'user', 'content_type', 'created_at']
    search_fields = ['object_repr', 'object_id', 'user__email', 'school__name']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'school', 'user', 'action', 'content_type', 'object_id', 'object_repr',
        'field', 'before', 'after', 'ip_address', 'user_agent', 'created_at',
    ]
    actions = None  # audit log is append-only

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
