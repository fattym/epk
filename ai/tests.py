from datetime import date

from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from academics.models import Grade, Stream, Term, LearningArea, Enrollment, TeacherAssignment
from ai.models import AtRiskFlag
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f'School {code}', code=code, address='A', phone='1', email=f'{code}@school.com', website='https://school.com',
    )


def make_user(email, role, school, **kw):
    return User.objects.create_user(email=email, password='Password123!', role=role, school=school, **kw)


class AiRBACTests(APITestCase):
    def setUp(self):
        self.school = make_school('AI')
        self.admin = make_user('admin@ai.com', 'ADMIN', self.school)
        self.parent = make_user('p@ai.com', 'PARENT', self.school, first_name='P', last_name='One')
        self.teacher = make_user('t@ai.com', 'TEACHER', self.school)
        self.student = make_user('s@ai.com', 'STUDENT', self.school)
        self.grade = Grade.objects.create(name='Grade 1', stage='primary', order=1)
        self.stream = Stream.objects.create(name='1A', grade=self.grade, school=self.school)
        Enrollment.objects.create(student=self.student, stream=self.stream, school=self.school)
        Term.objects.create(
            name='T1', start_date=date(2026, 1, 1), end_date=date(2026, 4, 30),
            academic_year='2025-2026', school=self.school, is_current=True,
        )
        from accounts.models import ParentLearner
        ParentLearner.objects.create(parent=self.parent, learner=self.student, school=self.school)

    def test_chatbot_requires_parent(self):
        client = APIClient()
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/ai/chatbot/', {'question': 'How am I?'})
        self.assertEqual(resp.status_code, 403)

    def test_chatbot_returns_answer(self):
        self.client.force_authenticate(user=self.parent)
        resp = self.client.post('/api/ai/chatbot/', {'question': 'What is the fee balance?'})
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertIn('answer', resp.json())

    def test_chatbot_no_question_fails(self):
        self.client.force_authenticate(user=self.parent)
        resp = self.client.post('/api/ai/chatbot/', {})
        self.assertEqual(resp.status_code, 400)

    def test_report_narrative_can_request_current_user(self):
        self.client.force_authenticate(user=self.student)
        resp = self.client.get('/api/ai/report-narrative/me/')
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertIn('narrative', resp.json())

    def test_report_narrative_requires_auth(self):
        client = APIClient()
        resp = client.get('/api/ai/report-narrative/me/')
        self.assertEqual(resp.status_code, 401)

    def test_moderation_requires_text(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/ai/moderate/', {})
        self.assertEqual(resp.status_code, 400)

    def test_moderation_returns_result(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/ai/moderate/', {'text': 'Hello world'})
        self.assertEqual(resp.status_code, 200, resp.json())
