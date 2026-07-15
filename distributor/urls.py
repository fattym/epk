from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DistributorProfileViewSet, DistributorProductViewSet, SchoolOrderViewSet, DeliveryViewSet

router = DefaultRouter()
router.register(r'profiles', DistributorProfileViewSet, basename='distributorprofile')
router.register(r'products', DistributorProductViewSet, basename='distributorproduct')
router.register(r'orders', SchoolOrderViewSet, basename='schoolorder')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')

urlpatterns = [
    path('', include(router.urls)),
]
