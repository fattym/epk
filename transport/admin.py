from django.contrib import admin
from .models import Route, BusStop, Bus, BusAssignment


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'is_active', 'created_at']
    list_filter = ['school', 'is_active']
    search_fields = ['name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)


@admin.register(BusStop)
class BusStopAdmin(admin.ModelAdmin):
    list_display = ['name', 'route', 'school', 'order', 'is_active']
    list_filter = ['school', 'is_active', 'route']
    search_fields = ['name', 'route__name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = [
        'plate_number', 'school', 'driver', 'route', 'model',
        'capacity', 'is_active', 'last_location_update',
    ]
    list_filter = ['school', 'is_active', 'route']
    search_fields = ['plate_number', 'driver__email']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)


@admin.register(BusAssignment)
class BusAssignmentAdmin(admin.ModelAdmin):
    list_display = ['bus', 'student', 'school', 'start_date', 'end_date', 'is_active']
    list_filter = ['school', 'is_active', 'bus']
    search_fields = ['bus__plate_number', 'student__email']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(school=request.user.school)
