from rest_framework import serializers
from .models import (
    CompetencyAssessment,
    LearnerPortfolio,
    AssessmentEvidence,
    AssessmentTask,
    AssessmentTaskResult,
    teacher_can_assess,
)


class AssessmentEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentEvidence
        fields = ['id', 'assessment', 'file', 'evidence_type', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    evidence = AssessmentEvidenceSerializer(many=True, read_only=True)
    learning_area = serializers.SerializerMethodField()
    strand = serializers.SerializerMethodField()
    sub_strand = serializers.SerializerMethodField()
    learner_name = serializers.SerializerMethodField()
    competency_score = serializers.SerializerMethodField()
    assessed_by = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CompetencyAssessment
        fields = '__all__'
        read_only_fields = ['assessed_at', 'assessed_by']

    def get_learning_area(self, obj):
        try:
            return obj.outcome.sub_strand.strand.learning_area.name
        except Exception:
            return None

    def get_strand(self, obj):
        try:
            return obj.outcome.sub_strand.strand.name
        except Exception:
            return None

    def get_sub_strand(self, obj):
        try:
            return obj.outcome.sub_strand.name
        except Exception:
            return None

    def get_learner_name(self, obj):
        return f"{obj.learner.first_name} {obj.learner.last_name}" if obj.learner_id else None

    def get_competency_score(self, obj):
        level = (obj.level_achieved or '').upper()
        mapping = {'EE': 4, 'ME': 3, 'AE': 2, 'BE': 1}
        value = mapping.get(level)
        return value

    def get_assessed_by(self, obj):
        try:
            return obj.assessed_by.email if obj.assessed_by_id else None
        except Exception:
            return None

    def get_status(self, obj):
        level = obj.level_achieved or ''
        return {
            'EE': 'Exceeding Expectations',
            'ME': 'Meeting Expectation',
            'AE': 'Approaching Expectation',
            'BE': 'Below Expectation',
        }.get(level, level or 'Draft')

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


class AssessmentTaskResultSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentTaskResult
        fields = ['id', 'learner', 'learner_name', 'level_achieved', 'remark']

    def get_learner_name(self, obj):
        return f"{obj.learner.first_name} {obj.learner.last_name}" if obj.learner_id else None


class AssessmentTaskSerializer(serializers.ModelSerializer):
    learning_area_name = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    results = AssessmentTaskResultSerializer(many=True, required=False)

    class Meta:
        model = AssessmentTask
        fields = [
            'id', 'learning_area', 'learning_area_name', 'term', 'title', 'task_type',
            'strand', 'sub_strand', 'created_by', 'created_by_email', 'status',
            'created_at', 'results',
        ]
        read_only_fields = ['created_by', 'created_at']

    def get_learning_area_name(self, obj):
        try:
            return obj.learning_area.name
        except Exception:
            return None

    def get_created_by_email(self, obj):
        try:
            return obj.created_by.email if obj.created_by_id else None
        except Exception:
            return None

    def create(self, validated_data):
        results_data = validated_data.pop('results', [])
        request = self.context.get('request')
        if request and not validated_data.get('created_by_id'):
            validated_data['created_by'] = request.user
        task = AssessmentTask.objects.create(**validated_data)
        for item in results_data:
            AssessmentTaskResult.objects.create(task=task, **item)
        return task
