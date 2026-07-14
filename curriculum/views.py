from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from academics.models import SubStrand, LearningOutcome, Strand
from .models import ReferenceDocument, SchemeOfWork, SchemeWeek
from .serializers import ReferenceDocumentSerializer, SchemeOfWorkSerializer, SchemeGenerateSerializer


class ReferenceDocumentViewSet(viewsets.ModelViewSet):
    queryset = ReferenceDocument.objects.all()
    serializer_class = ReferenceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return ReferenceDocument.objects.filter(school=user.school)
        return ReferenceDocument.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user, school=self.request.user.school)


class SchemeOfWorkViewSet(viewsets.ModelViewSet):
    queryset = SchemeOfWork.objects.all()
    serializer_class = SchemeOfWorkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'TEACHER':
            return SchemeOfWork.objects.filter(teacher=user)
        return SchemeOfWork.objects.filter(school=user.school)

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user, school=self.request.user.school)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        serializer = SchemeGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        learning_area_id = serializer.validated_data['learning_area']
        term_id = serializer.validated_data['term']
        stream_id = serializer.validated_data['stream']

        from academics.models import LearningArea, Term, Stream
        try:
            learning_area = LearningArea.objects.get(id=learning_area_id)
            term = Term.objects.get(id=term_id)
            stream = Stream.objects.get(id=stream_id)
        except (LearningArea.DoesNotExist, Term.DoesNotExist, Stream.DoesNotExist):
            return Response({'detail': 'Invalid learning area, term, or stream'}, status=status.HTTP_400_BAD_REQUEST)

        scheme, created = SchemeOfWork.objects.get_or_create(
            teacher=request.user,
            learning_area=learning_area,
            term=term,
            stream=stream,
            school=request.user.school,
            defaults={'status': 'draft'},
        )

        if created:
            strands = Strand.objects.filter(learning_area=learning_area).prefetch_related('sub_strands')
            week_num = 1
            for strand in strands:
                for sub_strand in strand.sub_strands.all():
                    outcomes = LearningOutcome.objects.filter(sub_strand=sub_strand)
                    outcome_text = '; '.join([o.description for o in outcomes[:3]])
                    if not outcome_text:
                        outcome_text = sub_strand.name
                    SchemeWeek.objects.create(
                        scheme=scheme,
                        week_number=week_num,
                        strand=strand,
                        sub_strand=sub_strand,
                        specific_learning_outcomes=outcome_text,
                    )
                    week_num += 1

        result_serializer = SchemeOfWorkSerializer(scheme)
        return Response(result_serializer.data, status=status.HTTP_200_OK)
