from django.db.models import Count, Avg, Q, Sum
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from academics.models import Stream, LearningArea, TeacherAssignment, Enrollment, Grade, Term
from assessment.models import CompetencyAssessment, AssessmentTask
from attendance.models import AttendanceRecord
from exams.models import Exam, ExamGrade
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
        learner__school=school, level_achieved__in=['ME', 'EE']
    ).count()
    total_ass = CompetencyAssessment.objects.filter(learner__school=school).count()

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


# === Education Analytics Dashboard Endpoints ===

LEVEL_SCORE = {'BE': 1, 'AE': 2, 'ME': 3, 'EE': 4}
LEVEL_LABELS = {'BE': 'Below Expectation', 'AE': 'Approaching Expectation', 'ME': 'Meeting Expectation', 'EE': 'Exceeding Expectation'}


def _safe_school(user):
    """Return the user's school or None (used for permission scoping)."""
    return getattr(user, 'school', None)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_kpis(request):
    """Aggregated KPIs for the analytics dashboard."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    today = date.today()

    # Total enrolled students (active enrollments)
    total_students = Enrollment.objects.filter(school=school, is_active=True).count()

    # Students present today
    present_today = AttendanceRecord.objects.filter(
        school=school, date=today, status='PRESENT'
    ).count()

    # Total attendance records today (present + absent + late + excused)
    today_att_total = AttendanceRecord.objects.filter(school=school, date=today).count()
    att_pct_today = round(present_today / today_att_total * 100, 1) if today_att_total else 0

    # Average exam performance (% of total marks)
    grades = ExamGrade.objects.filter(school=school)
    avg_exam_pct = round(grades.aggregate(avg=Avg('marks_obtained'))['avg'] or 0, 1)

    # Active teachers
    active_teachers = User.objects.filter(school=school, role='TEACHER').count()

    # Assessments awaiting marking (AssessmentTask with status ACTIVE)
    pending_assessments = AssessmentTask.objects.filter(
        learning_area__school=school, status='ACTIVE'
    ).count()

    return Response({
        'total_students': total_students,
        'students_present_today': present_today,
        'attendance_percentage_today': att_pct_today,
        'avg_academic_performance': avg_exam_pct,
        'active_teachers': active_teachers,
        'assessments_awaiting_marking': pending_assessments,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_by_subject(request):
    """Average exam performance by learning area (subject)."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    term_id = request.query_params.get('term')
    stream_id = request.query_params.get('stream')

    grades = ExamGrade.objects.filter(exam__school=school)
    exams = Exam.objects.filter(school=school)

    if term_id:
        try:
            term = Term.objects.get(id=term_id, school=school)
            exams = exams.filter(learning_area__isnull=False)
        except Term.DoesNotExist:
            return Response({'detail': 'Invalid term.'}, status=status.HTTP_400_BAD_REQUEST)

    if stream_id:
        try:
            exams = exams.filter(stream_id=stream_id)
        except (ValueError, Stream.DoesNotExist):
            return Response({'detail': 'Invalid stream.'}, status=status.HTTP_400_BAD_REQUEST)

    grades = grades.filter(exam__in=exams)

    data = grades.values('exam__learning_area__name').annotate(
        avg_marks=Avg('marks_obtained'),
        total=Avg('exam__total_marks'),
        count=Count('id'),
    ).order_by('-avg_marks')

    return Response([
        {
            'subject': item['exam__learning_area__name'],
            'average_percentage': round(item['avg_marks'] / item['total'] * 100, 1) if item['total'] else 0,
            'assessment_count': item['count'],
        }
        for item in data
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_by_class(request):
    """Average exam performance by class (stream)."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    grades = ExamGrade.objects.filter(exam__school=school)

    data = grades.values('exam__stream__name').annotate(
        avg_marks=Avg('marks_obtained'),
        total=Avg('exam__total_marks'),
        count=Count('id'),
    ).order_by('-avg_marks')

    return Response([
        {
            'class': item['exam__stream__name'],
            'average_percentage': round(item['avg_marks'] / item['total'] * 100, 1) if item['total'] else 0,
            'assessment_count': item['count'],
        }
        for item in data
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def progress_over_terms(request):
    """Average performance across academic terms."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    terms = Term.objects.filter(school=school).order_by('start_date')

    data = []
    for term in terms:
        term_exams = Exam.objects.filter(school=school).filter(
            date__gte=term.start_date, date__lte=term.end_date
        )
        term_grades = ExamGrade.objects.filter(exam__in=term_exams)
        avg_marks = term_grades.aggregate(avg=Avg('marks_obtained'))['avg']
        avg_total = term_grades.aggregate(avg=Avg('exam__total_marks'))['avg']
        pct = round(avg_marks / avg_total * 100, 1) if avg_total else 0
        data.append({
            'term': term.name,
            'academic_year': term.academic_year,
            'average_percentage': pct,
            'exam_count': term_exams.count(),
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_distribution(request):
    """Distribution of competency assessment levels (CBC BE/AE/ME/EE)."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    counts = CompetencyAssessment.objects.filter(
        learner__school=school
    ).values('level_achieved').annotate(count=Count('id'))

    distribution = {key: 0 for key in LEVEL_LABELS}
    for item in counts:
        level = item['level_achieved']
        if level in distribution:
            distribution[level] = item['count']

    total = sum(distribution.values())
    result = []
    for level, label in LEVEL_LABELS.items():
        count = distribution.get(level, 0)
        result.append({
            'level': level,
            'label': label,
            'count': count,
            'percentage': round(count / total * 100, 1) if total else 0,
        })

    return Response({
        'total_assessments': total,
        'distribution': result,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_trend_chart(request):
    """Daily attendance trend for the last N days."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    days = int(request.query_params.get('days', 30))
    days = min(days, 90)
    start_date = date.today() - timedelta(days=days)

    att_data = AttendanceRecord.objects.filter(
        school=school, date__gte=start_date
    ).values('date', 'status').annotate(count=Count('id')).order_by('date')

    # Build a map of date -> {present, absent, late, excused, total}
    by_date = {}
    for row in att_data:
        d = row['date']
        if d not in by_date:
            by_date[d] = {'date': d.isoformat(), 'present': 0, 'absent': 0, 'late': 0, 'excused': 0, 'total': 0}
        by_date[d][row['status'].lower()] = row['count']
        by_date[d]['total'] += row['count']

    # Fill in missing dates with null
    labels = []
    present_data = []
    absent_data = []
    late_data = []
    pct_data = []
    for i in range(days, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        labels.append(d)
        if d in by_date:
            day_data = by_date[d]
            present_data.append(day_data['present'])
            absent_data.append(day_data['total'] - day_data['present'] - day_data['late'] - day_data['excused'])
            late_data.append(day_data['late'])
            pct_data.append(round(day_data['present'] / day_data['total'] * 100, 1) if day_data['total'] else 0)
        else:
            present_data.append(None)
            absent_data.append(None)
            late_data.append(None)
            pct_data.append(None)

    return Response({
        'labels': labels,
        'present': present_data,
        'absent': absent_data,
        'late': late_data,
        'percentage': pct_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def marking_completion(request):
    """Assessment marking completion status by learning area."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    tasks = AssessmentTask.objects.filter(learning_area__school=school)
    data = []
    for task in tasks:
        total_results = task.results.count()
        data.append({
            'id': task.id,
            'learning_area': task.learning_area.name if task.learning_area else 'N/A',
            'term': task.term.name if task.term else 'N/A',
            'title': task.title,
            'task_type': task.get_task_type_display(),
            'status': task.status,
            'results_count': total_results,
        })

    data.sort(key=lambda x: x['results_count'])

    return Response({
        'total_tasks': len(data),
        'incomplete_count': len([d for d in data if d['results_count'] == 0]),
        'tasks': data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def at_risk_students(request):
    """Students flagged for attention based on attendance and performance thresholds."""
    school = _safe_school(request.user)
    if not school:
        return Response({'detail': 'User has no school assigned.'}, status=status.HTTP_403_FORBIDDEN)

    attendance_threshold = int(request.query_params.get('absence_threshold', 5))
    perf_threshold = int(request.query_params.get('low_perf_threshold', 40))

    # Students with repeated absences (using AttendanceSummary)
    from attendance.models import AttendanceSummary
    low_attendance = AttendanceSummary.objects.filter(
        school=school, absent_days__gte=attendance_threshold
    ).select_related('student', 'stream')

    flagged = set()
    for summary in low_attendance:
        flagged.add(summary.student_id)

    # Students with below-threshold exam performance
    low_perf_grades = ExamGrade.objects.filter(
        exam__school=school
    ).values('student').annotate(
        avg_score=Avg('marks_obtained')
    ).filter(avg_score__lt=perf_threshold)
    for item in low_perf_grades:
        flagged.add(item['student'])

    # Build response
    students = User.objects.filter(id__in=flagged, school=school)
    enrollments = Enrollment.objects.filter(
        student__in=students, is_active=True
    ).select_related('stream').in_bulk(field_name='student_id')

    result = []
    for s in students:
        enr = enrollments.get(s.id)
        att_summary = AttendanceSummary.objects.filter(student=s, school=school).first()
        avg_exam = ExamGrade.objects.filter(student=s, exam__school=school).aggregate(
            avg=Avg('marks_obtained')
        )['avg']
        result.append({
            'id': s.id,
            'name': _name(s),
            'stream': enr.stream.name if enr else None,
            'avg_exam_score': round(avg_exam, 1) if avg_exam else 0,
            'absent_days': att_summary.absent_days if att_summary else 0,
            'flags': [
                'low_attendance' if att_summary and att_summary.absent_days >= attendance_threshold else None,
                'low_performance' if avg_exam and avg_exam < perf_threshold else None,
            ],
        })

    return Response({
        'attendance_threshold': attendance_threshold,
        'perf_threshold': perf_threshold,
        'total_flagged': len(result),
        'students': result,
    })
