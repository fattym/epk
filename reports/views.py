from django.db.models import Count, Avg, Q
from datetime import date
from decimal import Decimal

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from academics.models import Stream, LearningArea, TeacherAssignment, Enrollment
from attendance.models import AttendanceRecord
from exams.models import Exam, ExamGrade
from assessment.models import CompetencyAssessment
from fees.models import Invoice
from complaints.models import Complaint
from events.models import Event
from homework.models import Homework


def _name(u):
    return f'{u.first_name} {u.last_name}'.strip() or u.email


def overview_data(school):
    students = User.objects.filter(school=school, role='STUDENT')
    teachers = User.objects.filter(school=school, role='TEACHER')
    streams = Stream.objects.filter(school=school)
    areas = LearningArea.objects.filter(school=school)

    att = AttendanceRecord.objects.filter(school=school).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        absent=Count('id', filter=Q(status='ABSENT')),
        late=Count('id', filter=Q(status='LATE')),
        total=Count('id'),
    )
    total_att = att['total'] or 0
    present = att['present'] or 0
    att_pct = round(present / total_att * 100, 1) if total_att else 0

    inv = Invoice.objects.filter(school=school)
    expected = sum((i.amount for i in inv), Decimal(0))
    collected = sum((i.amount for i in inv.filter(status='PAID')), Decimal(0))
    overdue = inv.filter(status='OVERDUE').count()
    fee_rate = round(collected / expected * 100, 1) if expected else 0

    grades = ExamGrade.objects.filter(school=school)
    avg_exam = grades.aggregate(avg=Avg('marks_obtained'))['avg']
    avg_exam = round(avg_exam, 1) if avg_exam else 0
    me_ee = CompetencyAssessment.objects.filter(
        school=school, level_achieved__in=['ME', 'EE']
    ).count()
    total_ass = CompetencyAssessment.objects.filter(school=school).count()

    return {
        'students': students.count(),
        'teachers': teachers.count(),
        'classes': streams.count(),
        'subjects': areas.count(),
        'pending_complaints': Complaint.objects.filter(school=school, status='Pending').count(),
        'events': Event.objects.filter(school=school).count(),
        'homeworks': Homework.objects.filter(school=school).count(),
        'attendance': {**att, 'present_pct': att_pct},
        'fee_collection': {
            'expected': float(expected), 'collected': float(collected),
            'overdue': overdue, 'rate': fee_rate,
        },
        'performance': {
            'avg_exam_pct': avg_exam,
            'assessments_me_ee': me_ee,
            'assessments_total': total_ass,
        },
    }


def attendance_data(school):
    today = date.today()
    data = []
    for i in range(5, -1, -1):
        idx = (today.month - 1 - i) % 12
        y = today.year + (today.month - 1 - i) // 12
        m = idx + 1
        recs = AttendanceRecord.objects.filter(school=school, date__year=y, date__month=m)
        total = recs.count()
        present = recs.filter(status='PRESENT').count()
        pct = round(present / total * 100, 1) if total else 0
        data.append({
            'year': y, 'month': m,
            'label': date(y, m, 1).strftime('%b %Y'),
            'present_pct': pct, 'total': total,
        })
    return data


def results_data(school):
    exams = Exam.objects.filter(school=school).order_by('-date')[:25]
    data = []
    for ex in exams:
        grades = ExamGrade.objects.filter(exam=ex)
        total = grades.count()
        failed = grades.filter(grade='F').count()
        avg = grades.aggregate(avg=Avg('marks_obtained'))['avg']
        data.append({
            'id': ex.id,
            'name': ex.name,
            'stream': ex.stream.name if ex.stream else None,
            'learning_area': ex.learning_area.name if ex.learning_area else None,
            'date': ex.date.isoformat() if ex.date else None,
            'total': total, 'passed': total - failed, 'failed': failed,
            'avg_marks': round(avg, 1) if avg else 0,
        })
    return data


def performance_data(school):
    students = User.objects.filter(school=school, role='STUDENT')
    data = []
    for s in students:
        grades = ExamGrade.objects.filter(student=s)
        avg = grades.aggregate(avg=Avg('marks_obtained'))['avg']
        me_ee = CompetencyAssessment.objects.filter(
            learner=s, level_achieved__in=['ME', 'EE']
        ).count()
        enr = Enrollment.objects.filter(student=s, is_active=True).first()
        data.append({
            'id': s.id,
            'name': _name(s),
            'stream': enr.stream.name if enr else None,
            'exams': grades.count(),
            'avg_pct': round(avg, 1) if avg else 0,
            'me_ee': me_ee,
        })
    data.sort(key=lambda x: x['avg_pct'] or 0, reverse=True)
    return data[:50]


def teachers_data(school):
    teachers = User.objects.filter(school=school, role='TEACHER')
    data = []
    for t in teachers:
        assignments = TeacherAssignment.objects.filter(teacher=t, is_active=True)
        streams = list(assignments.values_list('stream', flat=True))
        student_ids = Enrollment.objects.filter(
            stream_id__in=streams, is_active=True
        ).values_list('student', flat=True)
        avg = ExamGrade.objects.filter(
            student_id__in=student_ids
        ).aggregate(avg=Avg('marks_obtained'))['avg']
        data.append({
            'id': t.id,
            'name': _name(t),
            'classes': assignments.values('stream').distinct().count(),
            'subjects': assignments.values('learning_area').distinct().count(),
            'avg_student_pct': round(avg, 1) if avg else 0,
        })
    return data


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview(request):
    return Response(overview_data(request.user.school))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_trend(request):
    return Response(attendance_data(request.user.school))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def results(request):
    return Response(results_data(request.user.school))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance(request):
    return Response(performance_data(request.user.school))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teachers_report(request):
    return Response(teachers_data(request.user.school))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    import csv
    import io

    etype = request.query_params.get('type', 'results')
    buf = io.StringIO()
    w = csv.writer(buf)

    if etype == 'attendance':
        w.writerow(['Month', 'Present %', 'Total Records'])
        for row in attendance_data(request.user.school):
            w.writerow([row['label'], row['present_pct'], row['total']])
    elif etype == 'performance':
        w.writerow(['Student', 'Class', 'Exams', 'Avg Marks %', 'ME/EE Count'])
        for row in performance_data(request.user.school):
            w.writerow([row['name'], row['stream'] or '', row['exams'], row['avg_pct'], row['me_ee']])
    else:
        w.writerow(['Exam', 'Class', 'Subject', 'Date', 'Total', 'Passed', 'Failed', 'Avg Marks'])
        for row in results_data(request.user.school):
            w.writerow([
                row['name'], row['stream'] or '', row['learning_area'] or '',
                row['date'] or '', row['total'], row['passed'], row['failed'], row['avg_marks'],
            ])

    response = Response(buf.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{etype}_report.csv"'
    return response
