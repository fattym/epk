from django.urls import path
from rest_framework.routers import DefaultRouter

from .recruitment_ai import (
    ContentModerationView,
    InterviewQuestionGeneratorView,
    ParentChatbotView,
    ResumeScreeningView,
)
from .views import ReportCardNarrativeView

router = DefaultRouter()

urlpatterns = [
    path('report-narrative/<int:student_id>/', ReportCardNarrativeView.as_view(), name='report-narrative'),
    path('report-narrative/me/', ReportCardNarrativeView.as_view(), kwargs={'student_id': 'me'}, name='report-narrative-me'),
    path('chatbot/', ParentChatbotView.as_view(), name='chatbot'),
    path('interview-questions/<int:job_posting_id>/', InterviewQuestionGeneratorView.as_view(), name='interview-questions'),
    path('resume-screening/<int:application_id>/', ResumeScreeningView.as_view(), name='resume-screening'),
    path('moderate/', ContentModerationView.as_view(), name='content-moderation'),
]
