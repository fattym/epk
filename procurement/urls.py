from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssetViewSet,
    GoodsReceivedViewSet,
    PurchaseOrderItemViewSet,
    PurchaseOrderViewSet,
    StockItemViewSet,
    SupplierViewSet,
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-order-items', PurchaseOrderItemViewSet)
router.register(r'goods-received', GoodsReceivedViewSet)
router.register(r'stock', StockItemViewSet)
router.register(r'assets', AssetViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
