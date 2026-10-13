from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DistributorProfileViewSet, DistributorProductViewSet, SchoolOrderViewSet,
    DeliveryViewSet, WalletViewSet,
)

router = DefaultRouter()
router.register(r'profiles', DistributorProfileViewSet, basename='distributorprofile')
router.register(r'products', DistributorProductViewSet, basename='distributorproduct')
router.register(r'orders', SchoolOrderViewSet, basename='schoolorder')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'wallet', WalletViewSet, basename='distributorwallet')

urlpatterns = [
    path('', include(router.urls)),
]
