from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DiscoveryProductsView,
    InstitutionEnquiryView,
    ProductPublicViewSet,
    PublicCategoryListView,
    PublicDistributorListView,
    ShoppableVideoViewSet,
)

router = DefaultRouter()
router.register(r'products', ProductPublicViewSet, basename='public-product')
router.register(r'videos', ShoppableVideoViewSet, basename='shoppable-video')

urlpatterns = [
    path('discovery/', DiscoveryProductsView.as_view(), name='discovery-products'),
    path('distributors/', PublicDistributorListView.as_view(), name='public-distributors'),
    path('categories/', PublicCategoryListView.as_view(), name='public-categories'),
    path('institution-enquiries/', InstitutionEnquiryView.as_view(), name='institution-enquiry'),
    path('', include(router.urls)),
]
