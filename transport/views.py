from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.apps import apps

from .models import Route, BusStop, Bus, BusAssignment
from .serializers import (
    RouteSerializer, BusStopSerializer, BusSerializer, BusWriteSerializer,
    BusAssignmentSerializer, BusAssignmentWriteSerializer,
    DriverLocationSerializer, BusLocationSerializer,
)


class IsAdminOrDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['ADMIN', 'DRIVER']


class RouteViewSet(viewsets.ModelViewSet):
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Route.objects.none()

    def get_queryset(self):
        return Route.objects.filter(school=self.request.user.school)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RouteSerializer
        return RouteSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.school != self.request.user.school:
            return Response(
                {'detail': 'You do not have permission to edit this route.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.school != self.request.user.school:
            return Response(
                {'detail': 'You do not have permission to delete this route.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance.delete()


class BusStopViewSet(viewsets.ModelViewSet):
    serializer_class = BusStopSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = BusStop.objects.none()

    def get_queryset(self):
        user = self.request.user
        stops = BusStop.objects.filter(school=user.school)
        route_id = self.request.query_params.get('route')
        if route_id:
            stops = stops.filter(route_id=route_id)
        return stops

    def perform_create(self, serializer):
        route = serializer.validated_data['route']
        if route.school != self.request.user.school:
            raise permissions.PermissionDenied()
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        instance.delete()


class BusViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Bus.objects.none()

    def get_queryset(self):
        user = self.request.user
        buses = Bus.objects.filter(school=user.school)
        if user.role == 'DRIVER':
            buses = buses.filter(driver=user)
        return buses

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BusWriteSerializer
        return BusSerializer

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        instance.delete()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            bus = Bus.objects.get(id=response.data['id'])
            serializer = BusSerializer(bus, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            bus = Bus.objects.get(id=response.data['id'])
            serializer = BusSerializer(bus, context=self.get_serializer_context())
            return Response(serializer.data)
        return response

    @action(detail=True, methods=['post'], url_path='location')
    def update_location(self, request, pk=None):
        bus = self.get_object()
        user = request.user
        if user.role == 'DRIVER' and bus.driver != user:
            return Response(
                {'detail': 'You can only update the location of your assigned bus.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DriverLocationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        bus.current_latitude = serializer.validated_data['latitude']
        bus.current_longitude = serializer.validated_data['longitude']
        bus.last_location_update = timezone.now()
        bus.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])
        return Response({'status': 'location updated'})


class BusAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = BusAssignment.objects.none()

    def get_queryset(self):
        user = self.request.user
        assignments = BusAssignment.objects.filter(school=user.school)
        student_id = self.request.query_params.get('student')
        if student_id:
            assignments = assignments.filter(student_id=student_id)
        if user.role == 'PARENT':
            from accounts.models import ParentLearner
            child_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            assignments = assignments.filter(student_id__in=child_ids)
        elif user.role == 'STUDENT':
            assignments = assignments.filter(student=user)
        return assignments

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BusAssignmentWriteSerializer
        return BusAssignmentSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            assignment = BusAssignment.objects.get(id=response.data['id'])
            serializer = BusAssignmentSerializer(assignment, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            assignment = BusAssignment.objects.get(id=response.data['id'])
            serializer = BusAssignmentSerializer(assignment, context=self.get_serializer_context())
            return Response(serializer.data)
        return response

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)

    def perform_update(self, serializer):
        if serializer.instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if instance.school != self.request.user.school:
            raise permissions.PermissionDenied()
        instance.delete()


class BusLocationView(APIView):
    """
    Public endpoint — returns all active buses with their current location.
    Available to anyone, no authentication required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, school_id):
        buses = Bus.objects.filter(is_active=True, school_id=school_id)
        serializer = BusLocationSerializer(buses, many=True)
        return Response(serializer.data)


class DriverAssignmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'DRIVER':
            return Response(
                {'detail': 'Only drivers can access this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        bus = Bus.objects.filter(driver=user, is_active=True, school=user.school).first()
        if not bus:
            return Response({'detail': 'You are not assigned to any active bus.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BusSerializer(bus)
        return Response(serializer.data)
