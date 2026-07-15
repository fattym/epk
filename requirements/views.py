from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import RequiredItem, RequiredItemOption
from .serializers import RequiredItemSerializer, RequiredItemCreateSerializer, RequiredItemOptionSerializer


class RequiredItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['class_level', 'term', 'is_mandatory', 'is_published']

    def get_queryset(self):
        return RequiredItem.objects.filter(school=self.request.user.school).select_related('class_level', 'term').prefetch_related('options')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RequiredItemCreateSerializer
        return RequiredItemSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def add_option(self, request, pk=None):
        required_item = self.get_object()
        serializer = RequiredItemOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(required_item=required_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        required_item = self.get_object()
        required_item.is_published = True
        required_item.save()
        return Response({'detail': 'Item list published to parents.'})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        required_item = self.get_object()
        required_item.is_published = False
        required_item.save()
        return Response({'detail': 'Item list unpublished.'})

    @action(detail=False, methods=['get'])
    def auto_link_suggestions(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []})
        suggestions = RequiredItem.objects.filter(
            school=request.user.school,
            name__icontains=query,
        ).select_related('class_level', 'term')[:10]
        data = []
        for item in suggestions:
            data.append({
                'id': item.id,
                'name': item.name,
                'class_level': item.class_level.name,
                'term': item.term.name,
                'options_count': item.options.count(),
            })
        return Response({'results': data})


class RequiredItemOptionViewSet(viewsets.ModelViewSet):
    serializer_class = RequiredItemOptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['required_item', 'source_type', 'delivery_available']

    def get_queryset(self):
        return RequiredItemOption.objects.filter(required_item__school=self.request.user.school).select_related('required_item', 'distributor', 'linked_product')

    def perform_create(self, serializer):
        required_item = serializer.validated_data.get('required_item')
        if required_item.school != self.request.user.school:
            raise PermissionError('Cannot add option to another school\'s item.')
        serializer.save()


class PublicRequiredItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequiredItemSerializer
    permission_classes = [permissions.AllowAny]
    queryset = RequiredItem.objects.none()

    def get_queryset(self):
        queryset = RequiredItem.objects.filter(is_published=True).select_related('class_level', 'term').prefetch_related('options__distributor')
        learner_id = self.request.query_params.get('learner_id')
        if learner_id:
            queryset = queryset.filter(class_level__enrollments__student_id=learner_id, class_level__enrollments__is_active=True).distinct()
        return queryset
