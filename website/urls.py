from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteConfigViewSet, PublicWebsiteView

router = DefaultRouter()
router.register(r'config', WebsiteConfigViewSet, basename='website-config')

urlpatterns = [
    path('', include(router.urls)),
    path('public/<str:slug>/', PublicWebsiteView.as_view(), name='public-website'),
]
