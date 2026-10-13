from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from django.db import transaction
from academics.models import LearningOutcome, Term, LearningArea
from accounts.models import User

from .models import (
    CompetencyAssessment,
    LearnerPortfolio,
    AssessmentEvidence,
    AssessmentTask,
    AssessmentTaskResult,
    teacher_can_assess,
)
from accounts.models import ParentLearner
from .serializers import (
    CompetencyAssessmentSerializer,
    LearnerPortfolioSerializer,
    AssessmentEvidenceSerializer,
    AssessmentTaskSerializer,
    AssessmentTaskResultSerializer,
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
            return CompetencyAssessment.objects.filter(
                assessed_by=user, learner__school=user.school
            ).select_related('learner', 'outcome__sub_strand__strand__learning_area', 'assessed_by', 'term')
        if user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            return CompetencyAssessment.objects.filter(learner_id__in=learner_ids)
        if user.role == 'STUDENT':
            return CompetencyAssessment.objects.filter(learner=user)
        return CompetencyAssessment.objects.filter(learner__school=user.school)


class AssessmentTaskViewSet(viewsets.ModelViewSet):
    """Full CRUD for formative assessment tasks, school-scoped.

    CREATE accepts a nested `results` list (`{learner, level_achieved, remark}`)
    so the teacher can design a task and score learners in one request.
    Teachers may only see/create tasks for learning areas at their school.
    """
    queryset = AssessmentTask.objects.none()
    serializer_class = AssessmentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AssessmentTask.objects.filter(
            learning_area__school=user.school
        ).select_related('learning_area', 'term').prefetch_related('results')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='student-result', permission_classes=[permissions.IsAuthenticated])
    def student_result(self, request, pk=None):
        """A learner reads/submits their own result for a published task (school-scoped, self only)."""
        task = self.get_object()
        user = request.user
        if user.role != 'STUDENT':
            return Response({'detail': 'Only learners may submit a result here.'}, status=403)

        result, _ = AssessmentTaskResult.objects.get_or_create(task=task, learner=user)

        if request.method == 'GET':
            return Response(AssessmentTaskResultSerializer(result).data)

        serializer = AssessmentTaskResultSerializer(result, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, learner=user)
        return Response(serializer.data)


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
