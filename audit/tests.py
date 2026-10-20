from datetime import date, timedelta

from django.test import TestCase

from accounts.models import User
from academics.models import Enrollment, Grade, LearningArea, Stream, Term, TeacherAssignment
from assessment.models import CompetencyAssessment, LearnerPortfolio
from audit.models import AuditLog
from attendance.models import AttendanceRecord
from fees.models import FeeStructure, Invoice, Payment
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f'School {code}', code=code, address='A', phone='1', email=f'{code}@school.com', website='https://school.com',
    )


def make_user(email, role, school, **kw):
    return User.objects.create_user(email=email, password='Password123!', role=role, school=school, **kw)


class AuditLogSignalTests(TestCase):
    def setUp(self):
        self.school = make_school('A')
        self.admin = make_user('admin@a.com', 'ADMIN', self.school)

    def test_invoice_status_change_is_logged(self):
        grade = Grade.objects.create(name='Grade 1', stage='primary', order=1)
        stream = Stream.objects.create(name='1A', grade=grade, school=self.school)
        student = make_user('s@a.com', 'STUDENT', self.school)
        Enrollment.objects.create(student=student, stream=stream, school=self.school, is_active=True)
        fs = FeeStructure.objects.create(
            name='T1', stream=stream, amount=1000, frequency='TERMLY',
            due_date=date.today(), school=self.school,
        )
        invoice = Invoice.objects.create(
            student=student, fee_structure=fs, amount=1000,
            due_date=date.today(), status='PENDING', school=self.school,
        )
        logs = AuditLog.objects.filter(content_type__model='invoice')
        self.assertTrue(logs.filter(action='create').exists())

        invoice.status = 'PAID'
        invoice.save()
        self.assertTrue(logs.filter(action='update').exists())

    def test_log_action_helper_records_entry(self):
        from audit.signals import log_action
        before = {'status': 'PENDING'}
        after = {'status': 'PAID'}
        log_action(
            'ai_suggestion',
            model_cls=User,
            object_id=self.admin.id,
            field='narrative_draft',
            before=before,
            after=after,
            user=self.admin,
            school=self.school,
        )
        entry = AuditLog.objects.get(action='ai_suggestion')
        self.assertEqual(entry.field, 'narrative_draft')
        self.assertEqual(entry.before, before)


class AtRiskFlaggingTests(TestCase):
    def setUp(self):
        self.school = make_school('R')
        self.admin = make_user('admin@r.com', 'ADMIN', self.school)
        self.teacher = make_user('t@r.com', 'TEACHER', self.school)
        self.grade = Grade.objects.create(name='Grade 1', stage='primary', order=1)
        self.stream = Stream.objects.create(name='1A', grade=self.grade, school=self.school)
        self.term = Term.objects.create(
            name='Term 1', start_date=date(2026, 1, 1), end_date=date(2026, 4, 30),
            academic_year='2025-2026', school=self.school, is_current=True,
        )
        self.student = make_user('s@r.com', 'STUDENT', self.school, first_name='Sam', last_name='Kid')
        Enrollment.objects.create(student=self.student, stream=self.stream, school=self.school)
        TeacherAssignment.objects.create(
            teacher=self.teacher, stream=self.stream, term=self.term,
            role='subject_teacher', school=self.school,
        )

    def test_flag_raised_for_low_attendance(self):
        from ai.tasks import flag_at_risk_learners
        cutoff = date.today() - timedelta(days=30)
        for i in range(10):
            AttendanceRecord.objects.create(
                student=self.student, school=self.school, stream=self.stream,
                date=cutoff + timedelta(days=i), status='ABSENT',
                recorded_by=self.teacher,
            )
        result = flag_at_risk_learners()
        from ai.models import AtRiskFlag
        flag = AtRiskFlag.objects.filter(
            learner=self.student, flag_type='combined', school=self.school,
        ).first()
        self.assertIsNotNone(flag)
        self.assertIn('Attendance', flag.reason)

    def test_no_flag_for_good_attendance(self):
        from ai.tasks import flag_at_risk_learners
        from ai.models import AtRiskFlag
        cutoff = date.today() - timedelta(days=30)
        for i in range(10):
            AttendanceRecord.objects.create(
                student=self.student, school=self.school, stream=self.stream,
                date=cutoff + timedelta(days=i), status='PRESENT',
                recorded_by=self.teacher,
            )
        flag_at_risk_learners()
        self.assertFalse(AtRiskFlag.objects.filter(
            learner=self.student, school=self.school,
        ).exists())
