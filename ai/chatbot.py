"""Parent-facing AI chatbot — grounds answers in each parent's actual data.

The chatbot never guesses; it pulls real figures from the existing API models
(fee balance, upcoming events, child progress) and can additionally hand a
question off to the LLM for a free-text answer.  A full audit trail of the
tool calls is returned so responses are auditable (brief §4.3).
"""
from datetime import date, timedelta

from academics.models import Enrollment, LearningArea, Term
from accounts.models import ParentLearner, User
from attendance.models import AttendanceRecord
from events.models import Event
from fees.models import Invoice, Payment


def _parent_children(user):
    return list(
        ParentLearner.objects.filter(parent=user)
        .select_related('learner')
        .values_list('learner', flat=True)
    )


def _child_enrollment(user, learner_id):
    try:
        learner = User.objects.get(id=learner_id, school=user.school)
    except User.DoesNotExist:
        return None, None
    enrollment = Enrollment.objects.filter(student=learner, is_active=True).first()
    return learner, enrollment


def _fee_balance(user, learner_id):
    learner, _ = _child_enrollment(user, learner_id)
    if not learner:
        return None
    inv = Invoice.objects.filter(student=learner, school=user.school)
    expected = sum((i.amount for i in inv), 0)
    paid = sum((p.amount for p in Payment.objects.filter(invoice__in=inv, school=user.school)), 0)
    return round(float(expected - paid), 2)


def _child_progress(user, learner_id):
    """Return per-subject best competency level + avg exam % for the current term."""
    from assessment.models import CompetencyAssessment
    learner, enrollment = _child_enrollment(user, learner_id)
    if not learner:
        return None
    term = Term.objects.filter(is_current=True, school=user.school).first()
    if not term:
        term = Term.objects.filter(school=user.school).first()
    if not term:
        return {'term': None, 'subjects': []}

    areas = LearningArea.objects.filter(
        grade=enrollment.stream.grade if enrollment and enrollment.stream else None,
        school=user.school,
    )
    subjects = []
    for la in areas:
        assessments = CompetencyAssessment.objects.filter(
            learner=learner, term=term,
            outcome__sub_strand__strand__learning_area=la,
        )
        levels = [a.level_achieved for a in assessments]
        best = 'EE' if 'EE' in levels else (
            'ME' if 'ME' in levels else (
                'AE' if 'AE' in levels else ('BE' if 'BE' in levels else None)
            )
        )
        avg = exams_avg(learner, la, term)
        subjects.append({
            'subject': la.name,
            'best_competency': best,
            'avg_exam_pct': avg,
        })
    return {'term': term.name if term else None, 'subjects': subjects}


def exams_avg(learner, learning_area, term):
    from django.db.models import Avg

    from exams.models import ExamGrade
    qs = ExamGrade.objects.filter(
        student=learner,
        exam__learning_area=learning_area,
        exam__date__gte=term.start_date,
        exam__date__lte=term.end_date,
        school=learner.school,
    )
    avg = qs.aggregate(avg=Avg('marks_obtained'))['avg']
    return round(avg, 1) if avg else None


def _upcoming_events(user, limit=5):
    today = date.today()
    qs = Event.objects.filter(
        school=user.school,
        start_date__gte=today,
    ).order_by('start_date')[:limit]
    return [{'name': e.name, 'date': e.start_date.isoformat(), 'location': e.location} for e in qs]


def _attendance_trend(user, learner_id):
    learner, _ = _child_enrollment(user, learner_id)
    if not learner:
        return None
    cutoff = date.today() - timedelta(days=30)
    recs = AttendanceRecord.objects.filter(student=learner, date__gte=cutoff)
    total = recs.count()
    present = recs.filter(status='PRESENT').count()
    pct = round(present / total * 100, 1) if total else 0
    return {'period_days': total, 'present_pct': pct}


def answer_question(user, question, selected_child_id=None):
    """Answer a parent question, grounded in real data. Returns (answer, sources)."""
    children = _parent_children(user)
    child_id = selected_child_id or (children[0] if children else None)

    sources = []
    context_parts = []

    if child_id:
        balance = _fee_balance(user, child_id)
        if balance is not None:
            sources.append('fee_balance')
            context_parts.append(f"Fee balance for child {child_id}: KES {balance}")

        progress = _child_progress(user, child_id)
        if progress and progress['subjects']:
            sources.append('competency_assessment')
            subjects_str = ', '.join(
                f"{s['subject']}: {s['best_competency'] or 'N/A'} ({s['avg_exam_pct'] or 'N/A'}%)"
                for s in progress['subjects']
            )
            context_parts.append(f"Progress ({progress['term']}): {subjects_str}")

        att = _attendance_trend(user, child_id)
        if att:
            sources.append('attendance')
            context_parts.append(f"Attendance last 30 days: {att['present_pct']}% ({att['period_days']} records)")

    events = _upcoming_events(user)
    if events:
        sources.append('events')
        events_str = '; '.join(f"{e['name']} ({e['date']})" for e in events)
        context_parts.append(f"Upcoming events: {events_str}")

    context_text = '. '.join(context_parts) or 'No specific data available for this parent.'
    prompt = (
        f"You are a helpful school assistant. A parent is asking: '{question}'. "
        f"Below is verified data for their account. Answer concisely in plain language. "
        f"If a figure is needed but missing, say so rather than guessing.\n\nContext: {context_text}"
    )
    from .client import call_llm
    llm_answer = call_llm([{'role': 'user', 'content': prompt}], temperature=0.3)

    if llm_answer:
        answer = llm_answer
        source = 'llm_with_data'
    else:
        answer = _keyword_answer(question, context_parts)
        source = 'rules_fallback'

    return {
        'answer': answer,
        'source': source,
        'sources': sources,
        'child_id': child_id,
        'context': context_text,
    }


KEYWORDS = {
    'fee': 'fee_balance',
    'balance': 'fee_balance',
    'owe': 'fee_balance',
    'payment': 'fee_balance',
    'mpesa': 'fee_balance',
    'event': 'events',
    'announcement': 'events',
    'calendar': 'events',
    'progress': 'competency_assessment',
    'grade': 'competency_assessment',
    'result': 'competency_assessment',
    'mark': 'competency_assessment',
    'attendance': 'attendance',
    'present': 'attendance',
    'absent': 'attendance',
    'uniform': 'general',
    'size': 'general',
}


def _keyword_answer(question, context_parts):
    q = question.lower()
    for kw, topic in KEYWORDS.items():
        if kw in q:
            ctx = ' '.join(context_parts)
            if topic == 'fee_balance':
                return f"Your current fee balance is shown in the parent app under Fees. {ctx}"
            if topic == 'events':
                return f"Upcoming school events: {ctx}"
            if topic == 'competency_assessment':
                return f"Your child's academic progress: {ctx}"
            if topic == 'attendance':
                return f"Attendance information: {ctx}"
    return "I can help with fee balances, upcoming events, child progress, and attendance. Please ask a specific question."
