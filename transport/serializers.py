from rest_framework import serializers
from accounts.models import User
from .models import Route, BusStop, Bus, BusAssignment
from messaging.serializers import UserMiniSerializer


class BusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = ['id', 'route', 'school', 'name', 'latitude', 'longitude', 'order', 'is_active']
        read_only_fields = ['id', 'school']


class RouteSerializer(serializers.ModelSerializer):
    stops = BusStopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ['id', 'name', 'description', 'school', 'is_active', 'stops', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']


class BusSerializer(serializers.ModelSerializer):
    driver = UserMiniSerializer(read_only=True)
    route = RouteSerializer(read_only=True)

    class Meta:
        model = Bus
        fields = [
            'id', 'school', 'driver', 'route', 'plate_number', 'model',
            'capacity', 'is_active', 'current_latitude', 'current_longitude',
            'last_location_update', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']


class BusWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = [
            'id', 'school', 'driver', 'route', 'plate_number', 'model',
            'capacity', 'is_active',
        ]
        read_only_fields = ['id', 'school']


class BusAssignmentSerializer(serializers.ModelSerializer):
    student = UserMiniSerializer(read_only=True)
    bus = BusSerializer(read_only=True)

    class Meta:
        model = BusAssignment
        fields = ['id', 'bus', 'student', 'school', 'start_date', 'end_date', 'is_active', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']


class BusAssignmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusAssignment
        fields = ['id', 'bus', 'student', 'school', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['id', 'school']


class DriverLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class BusStopMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = ['id', 'name', 'latitude', 'longitude', 'order']


class BusLocationSerializer(serializers.ModelSerializer):
    stops = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'plate_number', 'route', 'current_latitude', 'current_longitude',
            'last_location_update', 'stops',
        ]

    def get_stops(self, obj):
        if obj.route:
            stops = obj.route.stops.filter(is_active=True)
            return BusStopMiniSerializer(stops, many=True).data
        return []
