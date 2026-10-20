from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrStaffOrTeacher

from .models import Asset, GoodsReceived, PurchaseOrder, PurchaseOrderItem, StockItem, Supplier
from .serializers import (
    AssetSerializer,
    GoodsReceivedSerializer,
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
    StockItemSerializer,
    SupplierSerializer,
)


class SchoolScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    school_filter_field = 'school'

    def get_queryset(self):
        return self.queryset.model.objects.filter(**{self.school_filter_field: self.request.user.school})


class SupplierViewSet(SchoolScopedViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    search_fields = ['name', 'contact_person', 'email']

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class PurchaseOrderViewSet(SchoolScopedViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    filterset_fields = ['status', 'supplier', 'created_at']
    search_fields = ['purpose', 'supplier__name']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        po = serializer.save()
        self._recalculate_total(po)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        valid_transition = {
            'PENDING': 'APPROVED',
            'DRAFT': 'APPROVED',
        }.get(po.status)
        if valid_transition is None:
            return Response({'detail': f'Cannot approve from {po.status}.'}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'APPROVED'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        chain = po.approval_chain or []
        chain.append({
            'step': len(chain) + 1,
            'role': request.user.role,
            'user_id': request.user.id,
            'approved_at': timezone.now().isoformat(),
        })
        po.approval_chain = chain
        po.save()
        return Response({'detail': 'Purchase order approved.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        po = self.get_object()
        if po.status not in ('PENDING', 'DRAFT'):
            return Response({'detail': f'Cannot reject from {po.status}.'}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'REJECTED'
        po.save()
        return Response({'detail': 'Purchase order rejected.'})

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        po = self.get_object()
        if po.status != 'APPROVED':
            return Response({'detail': 'Only approved purchase orders can be received.'}, status=status.HTTP_400_BAD_REQUEST)
        po.status = 'RECEIVED'
        po.received_at = timezone.now()
        po.save()
        self._restock(po)
        return Response({'detail': 'Goods received; stock updated.', 'items_received': len(po.items.all())})

    @staticmethod
    def _recalculate_total(po):
        total = sum(i.line_total for i in po.items.all())
        po.total_amount = total
        po.save()

    @staticmethod
    def _restock(po):
        """Add PO line items to stock on goods-receipt."""
        for item in po.items.all():
            stock, _ = StockItem.objects.get_or_create(
                school=po.school, name=item.description,
                defaults={'quantity_in_stock': 0, 'unit': 'piece'},
            )
            stock.quantity_in_stock += item.quantity
            stock.save()


class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseOrderItem.objects.filter(purchase_order__school=self.request.user.school)


class GoodsReceivedViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceived.objects.all()
    serializer_class = GoodsReceivedSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]

    def get_queryset(self):
        return GoodsReceived.objects.filter(purchase_order__school=self.request.user.school)


class StockItemViewSet(SchoolScopedViewSet):
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    search_fields = ['name', 'category']

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        from django.db.models import F
        items = self.get_queryset().filter(quantity_in_stock__lte=F('reorder_level'))
        return Response(self.get_serializer(items, many=True).data)

class AssetViewSet(SchoolScopedViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    search_fields = ['tag', 'name', 'serial_number']

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        asset = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        from accounts.models import User
        try:
            user = User.objects.get(id=user_id, school=request.user.school)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        asset.assigned_to = user
        asset.status = 'IN_USE'
        asset.save()
        return Response({'detail': f'Asset {asset.tag} assigned to {user.email}.'})
