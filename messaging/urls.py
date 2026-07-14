from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, DirectMessageViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet)
router.register(r'direct-messages', DirectMessageViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
