from django.contrib import admin

from .models import AtRiskFlag


@admin.register(AtRiskFlag)
class AtRiskFlagAdmin(admin.ModelAdmin):
    list_display = ['learner', 'school', 'flag_type', 'severity', 'created_at', 'resolved', 'acknowledged_at']
    list_filter = ['flag_type', 'severity', 'resolved', 'school', 'created_at']
    search_fields = ['learner__email', 'school__name']
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_acknowledged']
    readonly_fields = ['flag_type', 'reason', 'details', 'created_at']

    @admin.action(description='Mark selected flags as resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)

    @admin.action(description='Mark selected flags as acknowledged')
    def mark_acknowledged(self, request, queryset):
        queryset.update(acknowledged_by=request.user, acknowledged_at=timezone.now())

    def has_add_permission(self, request):
        return False


from django.utils import timezone  # noqa: E402
