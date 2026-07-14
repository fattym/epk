from rest_framework import serializers
from .models import CompetencyAssessment, LearnerPortfolio


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetencyAssessment
        fields = '__all__'
        read_only_fields = ['assessed_at']


class LearnerPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerPortfolio
        fields = '__all__'
