from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DisciplinaryAppealViewSet, DisciplinaryRecordViewSet

router = DefaultRouter()
router.register(r'records', DisciplinaryRecordViewSet, basename='disciplinaryrecord')
router.register(r'appeals', DisciplinaryAppealViewSet, basename='disciplinaryappeal')

urlpatterns = [
    path('', include(router.urls)),
]
