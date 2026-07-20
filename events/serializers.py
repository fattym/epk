from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'event_type', 'start_date', 'end_date',
            'location', 'is_holiday', 'created_by', 'created_by_name',
            'school', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'school', 'created_at']

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        u = obj.created_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email
