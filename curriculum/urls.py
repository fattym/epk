from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReferenceDocumentViewSet, SchemeOfWorkViewSet, SchemeWeekViewSet

router = DefaultRouter()
router.register(r'reference-documents', ReferenceDocumentViewSet)
router.register(r'schemes', SchemeOfWorkViewSet)
router.register(r'scheme-weeks', SchemeWeekViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
