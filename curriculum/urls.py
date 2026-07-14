from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReferenceDocumentViewSet, SchemeOfWorkViewSet

router = DefaultRouter()
router.register(r'reference-documents', ReferenceDocumentViewSet)
router.register(r'schemes', SchemeOfWorkViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
