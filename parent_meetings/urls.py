from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeetingNoteViewSet, ParentTeacherMeetingViewSet

router = DefaultRouter()
router.register(r'meetings', ParentTeacherMeetingViewSet, basename='parentteachermeeting')
router.register(r'notes', MeetingNoteViewSet, basename='meetingnote')

urlpatterns = [
    path('', include(router.urls)),
]
