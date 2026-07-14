from rest_framework import viewsets, permissions
from .models import CompetencyAssessment, LearnerPortfolio
from .serializers import CompetencyAssessmentSerializer, LearnerPortfolioSerializer


class CompetencyAssessmentViewSet(viewsets.ModelViewSet):
    queryset = CompetencyAssessment.objects.none()
    serializer_class = CompetencyAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'TEACHER':
            return CompetencyAssessment.objects.filter(assessed_by=user, learner__school=user.school)
        return CompetencyAssessment.objects.filter(learner__school=user.school)

    def perform_create(self, serializer):
        serializer.save(assessed_by=self.request.user)


class LearnerPortfolioViewSet(viewsets.ModelViewSet):
    queryset = LearnerPortfolio.objects.none()
    serializer_class = LearnerPortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['TEACHER', 'ADMIN']:
            return LearnerPortfolio.objects.filter(learner__school=user.school)
        return LearnerPortfolio.objects.filter(learner=user)
