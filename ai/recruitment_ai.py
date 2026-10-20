"""Chatbot, recruitment AI, and content-moderation endpoints."""
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsParent
from audit.signals import log_action
from recruitment.models import Application, JobPosting

from .chatbot import answer_question
from .client import call_llm


class ParentChatbotView(APIView):
    """Parent-facing AI chatbot anchored to the parent's own data.

    POST /api/ai/chatbot/
    {
        "question": "What is my fee balance?",
        "child_id": 42            # optional; defaults to first linked child
    }

    Responses include the ``sources`` list and ``context`` snapshot so the
    answer is auditable (brief §4.3 — tool-use against the DRF API surface).
    """
    permission_classes = [permissions.IsAuthenticated, IsParent]

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'detail': 'question is required.'}, status=status.HTTP_400_BAD_REQUEST)
        child_id = request.data.get('child_id')
        result = answer_question(request.user, question, selected_child_id=child_id)
        log_action(
            'create',
            model_cls=type(request.user),
            object_id=request.user.id,
            object_repr='chatbot interaction',
            field='chatbot',
            before={'question': question, 'child_id': child_id},
            after={'answer': result['answer'], 'sources': result['sources']},
        )
        return Response(result)


class InterviewQuestionGeneratorView(APIView):
    """Draft role-specific interview questions + scoring rubric for a job.

    POST /api/ai/interview-questions/{job_posting_id}/
    Returns a *draft* — hiring team reviews before using (brief §4.7).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_posting_id=None):
        posting = get_object_or_404(JobPosting, id=job_posting_id)
        if posting.school != request.user.school:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        num_questions = int(request.query_params.get('count', 5))

        prompt = (
            f"You are an experienced education recruiter in Kenya. For the position of "
            f"'{posting.title}' in the {posting.department or 'N/A'} department, "
            f"the key requirements are: {posting.requirements or 'not specified'}. "
            f"Generate {num_questions} behavioural/skills-based interview questions "
            f"aligned to these requirements, plus a simple 1-5 scoring rubric for "
            f"each question (1 = poor, 5 = excellent) with a one-line descriptor per level. "
            f"Respond in JSON: {{ \"questions\": [{{\"question\": \"...\", \"rubric\": [{{\"level\": 1, \"label\": \"...\"}}, ...]}}], ... }}"
        )
        answer = call_llm([{'role': 'user', 'content': prompt}], temperature=0.5)
        if not answer:
            answer = (
                "I cannot reach the AI service right now. Suggested generic questions: "
                "1. Tell me about yourself. 2. Why do you want to work here? "
                "3. Describe a time you handled a challenging student. "
                "4. How do you ensure fair assessment? 5. Where do you see yourself in 5 years?"
            )
        return Response({
            'job_posting': posting.title,
            'draft_questions': answer,
            'note': 'AI-generated draft. Review before sharing with interviewers.',
        })


class ResumeScreeningView(APIView):
    """Generate a structured fit summary for a candidate against a job.

    POST /api/ai/resume-screening/{application_id}/
    Augments — never replaces — human judgment (brief §4.4).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, application_id=None):
        application = get_object_or_404(Application, id=application_id)
        if application.school != request.user.school:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        posting = application.job_posting
        candidate = application.candidate

        requirements = posting.requirements or ''
        responsibilities = posting.responsibilities or ''
        cover = candidate.cover_letter or 'No cover letter provided.'

        prompt = (
            f"You are an HR screening assistant. For the position '{posting.title}' "
            f"requirements are: {requirements}. Responsibilities: {responsibilities}. "
            f"Candidate: {candidate.first_name} {candidate.last_name}. "
            f"Cover letter: {cover}. "
            f"Respond in JSON: {{ \"summary\": \"...\", \"fit_score\": <0-10>, "
            f"\"strengths\": [\"...\"], \"concerns\": [\"...\"], \"missing_requirements\": [\"...\"] }}. "
            f"fit_score 0-3 = weak, 4-6 = partial, 7-10 = strong. "
            f"Do NOT recommend automatic rejection."
        )
        answer = call_llm([{'role': 'user', 'content': prompt}], temperature=0.4)
        return Response({
            'candidate': f'{candidate.first_name} {candidate.last_name}',
            'job_posting': posting.title,
            'draft_summary': answer,
            'note': 'AI screening assist — human review required before any decision.',
        })


class ContentModerationView(APIView):
    """Screen free-text content for inappropriate material before human review.

    POST /api/ai/moderate/
    { "text": "..." }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        prompt = (
            f"Moderate the following text for a Kenyan school community. "
            f"Return JSON only: {{ \"flagged\": true/false, \"categories\": [\"hate\",\"bullying\",\"explicit\",\"spam\"], "
            f"\"severity\": \"low\"|\"medium\"|\"high\"|\"none\", \"reason\": \"...\", \"suggested_action\": \"approve\"|\"review\"|\"reject\" }}. "
            f"Text: {text[:2000]}"
        )
        answer = call_llm([{'role': 'user', 'content': prompt}], temperature=0.2)
        return Response({'result': answer, 'original_length': len(text)})
