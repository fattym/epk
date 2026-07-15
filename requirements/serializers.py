from rest_framework import serializers
from .models import RequiredItem, RequiredItemOption


class RequiredItemOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredItemOption
        fields = ['id', 'required_item', 'source_type', 'price', 'distributor', 'location', 'delivery_available', 'linked_product', 'linked_distributor_product', 'is_recommended', 'created_at']
        read_only_fields = ['id', 'created_at']


class RequiredItemSerializer(serializers.ModelSerializer):
    options = RequiredItemOptionSerializer(many=True, read_only=True)

    class Meta:
        model = RequiredItem
        fields = ['id', 'school', 'name', 'description', 'class_level', 'term', 'is_mandatory', 'allow_external_purchase', 'preferred_source', 'is_published', 'created_at', 'updated_at', 'options']
        read_only_fields = ['id', 'school', 'created_at', 'updated_at']


class RequiredItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredItem
        fields = ['id', 'name', 'description', 'class_level', 'term', 'is_mandatory', 'allow_external_purchase', 'preferred_source', 'is_published']
        read_only_fields = ['id']
