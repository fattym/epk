from celery import shared_task

from .models import AtRiskFlag


@shared_task
def flag_at_risk_learners():
    """Periodically scan for at-risk learners across attendance, competency
    and fee data.  Creates advisory AtRiskFlag records and notifies staff.

    Registered on Celery beat in core/celery.py.  Runs once per day.
    """
    from academics.models import Enrollment, Term
    from accounts.models import User
    from assessment.models import CompetencyAssessment
    from attendance.models import AttendanceRecord
    from fees.models import Invoice
    from messaging.models import Notification

    today = __import__('datetime').date.today()
    cutoff = today - __import__('datetime').timedelta(days=30)

    schools = User.objects.values_list('school', flat=True).distinct()
    total_flags = 0

    for school_id in schools:
        if not school_id:
            continue
        term = Term.objects.filter(is_current=True, school_id=school_id).first()

        students = User.objects.filter(school_id=school_id, role='STUDENT')
        for student in students:
            reasons = []
            details = {}
            severity = 'LOW'

            # --- Attendance: < 75% present in last 30 days ---
            att = AttendanceRecord.objects.filter(student=student, date__gte=cutoff)
            total = att.count()
            if total >= 5:
                present = att.filter(status='PRESENT').count()
                pct = round(present / total * 100, 1)
                details['attendance_pct'] = pct
                if pct < 75:
                    reasons.append(f'Attendance dropped to {pct}% over {total} records')
                    severity = 'HIGH' if pct < 60 else (severity if severity == 'HIGH' else 'MEDIUM')

            # --- Competency: repeated BE/AE ---
            assessments = CompetencyAssessment.objects.filter(
                learner=student,
                outcome__sub_strand__strand__learning_area__school_id=school_id,
            )
            if term:
                assessments = assessments.filter(term=term)
            total_ass = assessments.count()
            low_levels = assessments.filter(level_achieved__in=['BE', 'AE']).count()
            details['competency_total'] = total_ass
            details['competency_low'] = low_levels
            if total_ass >= 5 and low_levels / total_ass > 0.5:
                reasons.append(f'{low_levels}/{total_ass} competency assessments at Below/Accepting Expectation')
                if severity != 'HIGH':
                    severity = 'HIGH' if low_levels / total_ass > 0.7 else 'MEDIUM'

            # --- Fees: invoices overdue ---
            overdue = Invoice.objects.filter(
                student=student, school_id=school_id,
                status='OVERDUE',
            ).count()
            details['overdue_invoices'] = overdue
            if overdue > 0:
                reasons.append(f'{overdue} overdue invoice(s)')
                if severity == 'LOW':
                    severity = 'MEDIUM'

            if not reasons:
                continue

            flag, created = AtRiskFlag.objects.get_or_create(
                school_id=school_id,
                learner=student,
                flag_type='combined',
                resolved=False,
                defaults={
                    'severity': severity,
                    'reason': '; '.join(reasons),
                    'details': details,
                },
            )
            if created:
                total_flags += 1
                # Notify teachers in the student's stream
                enrollment = Enrollment.objects.filter(
                    student=student, is_active=True
                ).first()
                teacher_ids = []
                if enrollment:
                    from academics.models import TeacherAssignment
                    teacher_ids = list(
                        TeacherAssignment.objects.filter(
                            stream=enrollment.stream, is_active=True
                        ).values_list('teacher_id', flat=True)
                    )
                for tid in teacher_ids:
                    Notification.objects.create(
                        recipient_id=tid,
                        school_id=school_id,
                        title='At-risk learner alert',
                        message=f'{student.first_name} {student.last_name} has been flagged: {flag.reason}',
                    )

    return {'flags_created': total_flags}
