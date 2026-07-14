from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeeStructureViewSet, InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'fee-structures', FeeStructureViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
