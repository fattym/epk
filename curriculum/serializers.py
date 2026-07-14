from rest_framework import serializers
from .models import ReferenceDocument, SchemeOfWork, SchemeWeek


class ReferenceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceDocument
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at', 'school']


class SchemeWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemeWeek
        fields = '__all__'


class SchemeOfWorkSerializer(serializers.ModelSerializer):
    weeks = SchemeWeekSerializer(many=True, read_only=True)

    class Meta:
        model = SchemeOfWork
        fields = '__all__'
        read_only_fields = ['teacher', 'school']


class SchemeGenerateSerializer(serializers.Serializer):
    learning_area = serializers.IntegerField()
    term = serializers.IntegerField()
    stream = serializers.IntegerField()
