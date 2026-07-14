from rest_framework import serializers
from .models import (
    CompetencyAssessment,
    LearnerPortfolio,
    AssessmentEvidence,
    teacher_can_assess,
)


class AssessmentEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentEvidence
        fields = ['id', 'assessment', 'file', 'evidence_type', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    evidence = AssessmentEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = CompetencyAssessment
        fields = '__all__'
        read_only_fields = ['assessed_at', 'assessed_by']

    def validate(self, attrs):
        # Structurally prevent unassigned teachers from rating a learner (CBC accountability).
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        learner = attrs.get('learner') or (self.instance and self.instance.learner)
        outcome = attrs.get('outcome') or (self.instance and self.instance.outcome)
        term = attrs.get('term') or (self.instance and self.instance.term)
        if user and getattr(user, 'role', None) == 'TEACHER':
            if not (learner and outcome and term):
                raise serializers.ValidationError('learner, outcome and term are required.')
            learning_area = outcome.sub_strand.strand.learning_area
            if not teacher_can_assess(user, learner, learning_area, term):
                raise serializers.ValidationError(
                    'You are not assigned to teach this learner\'s class/subject for this term.'
                )
        return attrs

    def create(self, validated_data):
        # Idempotent: a retried offline write with the same client_uuid returns the original.
        client_uuid = validated_data.get('client_uuid')
        if client_uuid:
            existing = CompetencyAssessment.objects.filter(client_uuid=client_uuid).first()
            if existing:
                return existing
        request = self.context.get('request')
        assessed_by = request.user if request else None
        return CompetencyAssessment.objects.create(assessed_by=assessed_by, **validated_data)


class LearnerPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerPortfolio
        fields = '__all__'
