from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import PipelineStage, JobPosting, Candidate, Application, Interview, ScoreCard, Offer
from .serializers import (
    PipelineStageSerializer,
    JobPostingSerializer,
    CandidateSerializer,
    ApplicationSerializer,
    InterviewSerializer,
    ScoreCardSerializer,
    OfferSerializer,
)

User = get_user_model()


class PipelineStageViewSet(viewsets.ModelViewSet):
    queryset = PipelineStage.objects.none()
    serializer_class = PipelineStageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PipelineStage.objects.filter(school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school)


class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.none()
    serializer_class = JobPostingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'is_published', 'employment_type', 'department']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.school:
            return JobPosting.objects.filter(school=user.school)
        return JobPosting.objects.none()

    def perform_create(self, serializer):
        serializer.save(school=self.request.user.school, posted_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        queryset = JobPosting.objects.filter(is_active=True, is_published=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        posting = self.get_object()
        posting.is_published = True
        posting.save()
        return Response({'detail': 'Job posting published.'})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        posting = self.get_object()
        posting.is_published = False
        posting.save()
        return Response({'detail': 'Job posting unpublished.'})


class PublicApplicationViewSet(viewsets.GenericViewSet):
    queryset = Application.objects.none()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        honeypot = request.data.get('_honeypot')
        if honeypot:
            return Response({'detail': 'Invalid submission.'}, status=status.HTTP_400_BAD_REQUEST)

        job_posting = get_object_or_404(JobPosting, pk=request.data.get('job_posting'), is_active=True, is_published=True)
        if job_posting.application_deadline and job_posting.application_deadline < request.data.get('applied_at'):
            return Response({'detail': 'Application deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data, context={'is_public': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Application submitted successfully.'}, status=status.HTTP_201_CREATED)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.none()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'job_posting', 'candidate']

    def get_queryset(self):
        return Application.objects.filter(school=self.request.user.school)

    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        application = self.get_object()
        new_status = request.data.get('status')
        valid_transitions = {
            'APPLIED': ['SCREENING', 'REJECTED'],
            'SCREENING': ['INTERVIEW', 'REJECTED'],
            'INTERVIEW': ['OFFERED', 'REJECTED'],
            'OFFERED': ['HIRED', 'REJECTED'],
        }
        if new_status not in valid_transitions.get(application.status, []):
            return Response({'detail': f'Cannot transition from {application.status} to {new_status}.'}, status=status.HTTP_400_BAD_REQUEST)
        application.status = new_status
        application.save()
        return Response({'detail': f'Application status updated to {new_status}.'})


class InterviewViewSet(viewsets.ModelViewSet):
    queryset = Interview.objects.none()
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'application']

    def get_queryset(self):
        return Interview.objects.filter(application__school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScoreCardViewSet(viewsets.ModelViewSet):
    queryset = ScoreCard.objects.none()
    serializer_class = ScoreCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['interview', 'interviewer', 'recommendation']

    def get_queryset(self):
        return ScoreCard.objects.filter(interview__application__school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save()


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.none()
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']

    def get_queryset(self):
        return Offer.objects.filter(application__school=self.request.user.school)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.status != 'PENDING':
            return Response({'detail': 'Offer is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        if offer.expiry_date < request.data.get('accepted_at'):
            return Response({'detail': 'Offer has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        offer.status = 'ACCEPTED'
        offer.accepted_at = request.data.get('accepted_at')
        offer.save()

        application = offer.application
        application.status = 'HIRED'
        application.save()

        candidate = application.candidate
        email_base = candidate.email.split('@')[0]
        username = email_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{email_base}{counter}'
            counter += 1

        user = User.objects.create(
            username=username,
            email=candidate.email,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            role='STAFF',
            school=application.school,
            is_active=False,
        )
        user.set_unusable_password()
        user.save()

        return Response({'detail': 'Offer accepted. Onboarding user account created.', 'user_id': user.id})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        offer = self.get_object()
        if offer.status != 'PENDING':
            return Response({'detail': 'Offer is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        offer.status = 'DECLINED'
        offer.save()
        return Response({'detail': 'Offer declined.'})
