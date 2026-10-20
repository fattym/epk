
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Enrollment, Term
from accounts.models import ParentLearner, User
from assessment.models import CompetencyAssessment
from attendance.models import AttendanceRecord

from .client import call_llm

LEVEL_MAP = {
    'BE': 'Below Expectation',
    'AE': 'Approaching Expectation',
    'ME': 'Meeting Expectation',
    'EE': 'Exceeding Expectation',
}


def _name(user):
    return f'{user.first_name} {user.last_name}'.strip() or user.email or 'the learner'


def _competency_summary(learner, term, learning_area=None):
    qs = CompetencyAssessment.objects.filter(learner=learner, term=term)
    if learning_area:
        qs = qs.filter(outcome__sub_strand__strand__learning_area=learning_area)
    qs = qs.select_related('outcome__sub_strand__strand__learning_area')

    by_area = {}
    total = qs.count()
    me_ee = 0
    for ca in qs:
        la = ca.outcome.sub_strand.strand.learning_area
        la_id = la.id
        entry = by_area.setdefault(la_id, {
            'name': la.name, 'levels': [], 'count': 0, 'comments': [],
        })
        entry['levels'].append(ca.level_achieved)
        entry['count'] += 1
        entry['comments'].append(ca.teacher_comment)
        if ca.level_achieved in ('ME', 'EE'):
            me_ee += 1

    areas = []
    for la_id, data in by_area.items():
        best = 'EE' if 'EE' in data['levels'] else (
            'ME' if 'ME' in data['levels'] else (
                'AE' if 'AE' in data['levels'] else (
                    'BE' if 'BE' in data['levels'] else 'Unassessed'
                )
            )
        )
        areas.append({
            'learning_area': data['name'],
            'assessments': data['count'],
            'best_level': LEVEL_MAP.get(best, best),
        })

    return {
        'areas': areas,
        'total_assessments': total,
        'me_ee_count': me_ee,
        'me_ee_pct': round(me_ee / total * 100, 1) if total else 0,
    }


def _narrative_stub(learner, area, summary, attendance_pct):
    level = summary.get('best_level', 'mixed')
    assessments = area.get('assessments', summary.get('total_assessments', 0))
    return (
        f"{_name(learner)} has demonstrated {level.lower()} competency in {area['learning_area']} "
        f"this term ({assessments} assessments recorded, "
        f"attendance {attendance_pct}%). "
        "The learner is encouraged to continue practising the key concepts "
        "at home. Focus next term on consolidating the competencies marked as "
        "approaching or below expectation."
    )


def generate_report_narrative(learner, term, learning_area=None):
    """Compile the learner's CBC data then ask the LLM for a narrative.

    Never auto-saves — returns a *draft* string for teacher review (brief §4.2).
    """
    summary = _competency_summary(learner, term, learning_area)
    enrollment = Enrollment.objects.filter(student=learner, is_active=True).first()
    stream = enrollment.stream if enrollment else None
    grade = stream.grade if stream else None

    att = AttendanceRecord.objects.filter(student=learner, school=learner.school)
    if term:
        att = att.filter(date__gte=term.start_date, date__lte=term.end_date)
    total = att.count()
    present = att.filter(status='PRESENT').count()
    attendance_pct = round(present / total * 100, 1) if total else 0

    area_name = learning_area.name if learning_area else 'overall learning areas'
    areas_text = '; '.join(
        f"{a['learning_area']}: {a['assessments']} assessments, best={a['best_level']}"
        for a in summary['areas']
    ) or 'no competency data yet'

    prompt = (
        f"You are a Kenyan CBC teacher writing the end-of-term report narrative. "
        f"Learner: {_name(learner)}. Grade: {grade.name if grade else 'N/A'}. "
        f"Stream: {stream.name if stream else 'N/A'}. "
        f"Attendance: {attendance_pct}% present. "
        f"Competency summary ({area_name}): {areas_text}. "
        f"Overall: {summary['me_ee_pct']}% of assessments at Meeting/Exceeding Expectation. "
        f"Write 2-3 sentences in a supportive, family-friendly tone that a parent can understand. "
        f"Mention strengths and one actionable area for growth. Do NOT include the raw data tables — summarise in prose."
    )

    answer = call_llm([{'role': 'user', 'content': prompt}])
    if answer:
        return {
            'narrative': answer,
            'source': 'llm',
            'summary': summary,
            'attendance_pct': attendance_pct,
        }
    return {
        'narrative': _narrative_stub(learner, {'learning_area': area_name, 'assessments': summary['total_assessments']}, summary, attendance_pct),
        'source': 'fallback',
        'summary': summary,
        'attendance_pct': attendance_pct,
    }


class ReportCardNarrativeView(APIView):
    """Generate an AI-drafted narrative for a learner's report card.

    GET  /api/ai/report-narrative/{student_id}/?term_id={id}
    GET  /api/ai/report-narrative/me/?term_id={id}        (current user)

    The response is a *draft* only — it is not saved to the ReportCard model.
    Teachers paste/adjust it in the report-card UI before publishing.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id=None):
        user = request.user
        term_id = request.query_params.get('term_id')

        if student_id is None or student_id == 'me':
            student_id = user.id if user.role == 'STUDENT' else None
            if student_id is None and user.role == 'PARENT':
                link = ParentLearner.objects.filter(parent=user).first()
                student_id = link.learner_id if link else None

        if not student_id:
            return Response({'detail': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        student_id = int(student_id)
        if user.role == 'PARENT':
            ok = ParentLearner.objects.filter(parent=user, learner_id=student_id).exists()
            if not ok:
                return Response({'detail': 'You can only view your own children.'}, status=403)
        elif user.role == 'STUDENT' and student_id != user.id:
            return Response({'detail': 'You can only view your own report card.'}, status=403)

        try:
            student = User.objects.get(id=student_id, school=user.school)
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        if term_id:
            try:
                term = Term.objects.get(id=term_id, school=user.school)
            except Term.DoesNotExist:
                return Response({'detail': 'Term not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            term = Term.objects.filter(is_current=True, school=user.school).first() or Term.objects.filter(school=user.school).first()

        result = generate_report_narrative(student, term)
        return Response(result)
