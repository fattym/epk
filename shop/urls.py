from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductCategoryViewSet, ProductViewSet, ProductVariantViewSet, OrderViewSet, PublicProductViewSet, GuestOrderViewSet,
    chama_webhook, FormSubmissionViewSet,
)

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'public', PublicProductViewSet, basename='public-product')
router.register(r'variants', ProductVariantViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'guest-orders', GuestOrderViewSet, basename='guest-order')
router.register(r'form-submissions', FormSubmissionViewSet, basename='formsubmission')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/chama/', chama_webhook, name='chama-webhook'),
]
