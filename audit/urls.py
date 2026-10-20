from django.urls import include, path
from rest_framework import permissions, serializers, viewsets
from rest_framework.routers import DefaultRouter

from .models import AuditLog


class AuditLogReadSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    user = serializers.StringRelatedField()
    school = serializers.StringRelatedField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'created_at', 'action', 'school', 'user',
            'content_type', 'object_id', 'object_repr', 'field',
            'before', 'after', 'ip_address',
        ]
        read_only_fields = fields


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to the audit trail. Staff only."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action', 'school', 'content_type']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return AuditLog.objects.filter(school=user.school)
        return AuditLog.objects.none()


router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
