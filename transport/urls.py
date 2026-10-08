from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RouteViewSet, BusStopViewSet, BusViewSet,
    BusAssignmentViewSet, BusLocationView, DriverAssignmentView,
)

router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'stops', BusStopViewSet)
router.register(r'buses', BusViewSet)
router.register(r'assignments', BusAssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('locations/<int:school_id>/', BusLocationView.as_view(), name='bus-locations'),
    path('driver/assignment/', DriverAssignmentView.as_view(), name='driver-assignment'),
]
