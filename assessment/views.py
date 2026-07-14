from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from django.db import transaction
from academics.models import LearningOutcome, Term
from accounts.models import User

from .models import CompetencyAssessment, LearnerPortfolio, AssessmentEvidence, teacher_can_assess
from .serializers import (
    CompetencyAssessmentSerializer,
    LearnerPortfolioSerializer,
    AssessmentEvidenceSerializer,
)


class BulkAssessmentItemSerializer(serializers.Serializer):
    learner_id = serializers.IntegerField()
    level = serializers.CharField()
    comment = serializers.CharField(required=False, allow_blank=True)
    client_uuid = serializers.UUIDField(required=False)


class BulkAssessmentRequestSerializer(serializers.Serializer):
    outcome_id = serializers.IntegerField()
    term_id = serializers.IntegerField()
    assessments = BulkAssessmentItemSerializer(many=True)


class BulkAssessmentResultSerializer(serializers.Serializer):
    learner_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    detail = serializers.CharField(required=False, allow_null=True)
    assessment_id = serializers.IntegerField(required=False, allow_null=True)


class BulkAssessmentResponseSerializer(serializers.Serializer):
    results = BulkAssessmentResultSerializer(many=True)


class CompetencyAssessmentViewSet(viewsets.ModelViewSet):
    queryset = CompetencyAssessment.objects.none()
    serializer_class = CompetencyAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'TEACHER':
            return CompetencyAssessment.objects.filter(assessed_by=user, learner__school=user.school)
        return CompetencyAssessment.objects.filter(learner__school=user.school)


class LearnerPortfolioViewSet(viewsets.ModelViewSet):
    queryset = LearnerPortfolio.objects.none()
    serializer_class = LearnerPortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['TEACHER', 'ADMIN']:
            return LearnerPortfolio.objects.filter(learner__school=user.school)
        return LearnerPortfolio.objects.filter(learner=user)


class AssessmentEvidenceViewSet(viewsets.ModelViewSet):
    queryset = AssessmentEvidence.objects.all()
    serializer_class = AssessmentEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssessmentEvidence.objects.filter(assessment__learner__school=self.request.user.school)


class BulkAssessmentView(APIView):
    """POST /api/assessment/bulk/

    Gradebook-style bulk entry: one outcome + term, many learners.
    Idempotent via optional per-row client_uuid; re-submitting updates the existing row.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=BulkAssessmentRequestSerializer,
        responses={200: BulkAssessmentResponseSerializer},
    )
    def post(self, request):
        outcome_id = request.data.get('outcome_id')
        term_id = request.data.get('term_id')
        items = request.data.get('assessments', [])

        if not outcome_id or not term_id or not isinstance(items, list):
            return Response(
                {'detail': 'outcome_id, term_id and a list of assessments are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        try:
            outcome = LearningOutcome.objects.get(
                id=outcome_id, sub_strand__strand__learning_area__school=user.school
            )
        except LearningOutcome.DoesNotExist:
            return Response({'detail': 'Outcome not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            term = Term.objects.get(id=term_id, school=user.school)
        except Term.DoesNotExist:
            return Response({'detail': 'Term not found.'}, status=status.HTTP_404_NOT_FOUND)

        learning_area = outcome.sub_strand.strand.learning_area
        results = []

        with transaction.atomic():
            for item in items:
                learner_id = item.get('learner_id')
                level = item.get('level')
                comment = item.get('comment', '')
                client_uuid = item.get('client_uuid')

                if learner_id is None or not level:
                    results.append({'learner_id': learner_id, 'status': 'error',
                                    'detail': 'learner_id and level are required.'})
                    continue

                try:
                    learner = User.objects.get(id=learner_id, school=user.school, role='STUDENT')
                except User.DoesNotExist:
                    results.append({'learner_id': learner_id, 'status': 'error',
                                    'detail': 'Learner not found.'})
                    continue

                if user.role == 'TEACHER' and not teacher_can_assess(user, learner, learning_area, term):
                    results.append({'learner_id': learner_id, 'status': 'error',
                                    'detail': 'You are not assigned to teach this learner.'})
                    continue

                if client_uuid and CompetencyAssessment.objects.filter(client_uuid=client_uuid).exists():
                    existing = CompetencyAssessment.objects.get(client_uuid=client_uuid)
                    results.append({'learner_id': learner_id, 'status': 'existing',
                                    'assessment_id': existing.id})
                    continue

                obj, created = CompetencyAssessment.objects.get_or_create(
                    learner=learner,
                    outcome=outcome,
                    term=term,
                    defaults={
                        'level_achieved': level,
                        'teacher_comment': comment,
                        'assessed_by': user,
                        'client_uuid': client_uuid,
                    },
                )
                if not created:
                    obj.level_achieved = level
                    obj.teacher_comment = comment
                    obj.assessed_by = user
                    if client_uuid:
                        obj.client_uuid = client_uuid
                    obj.save()
                    results.append({'learner_id': learner_id, 'status': 'updated',
                                    'assessment_id': obj.id})
                else:
                    results.append({'learner_id': learner_id, 'status': 'created',
                                    'assessment_id': obj.id})

        return Response({'results': results}, status=status.HTTP_200_OK)
