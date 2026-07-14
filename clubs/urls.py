from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ClubSessionViewSet

router = DefaultRouter()
router.register(r'clubs', ClubViewSet)
router.register(r'sessions', ClubSessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
