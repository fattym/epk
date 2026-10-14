from datetime import date

from rest_framework.test import APITestCase

from academics.models import Grade, LearningArea, Term
from accounts.models import User
from assessment.models import AssessmentTask
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f"School {code}", code=code, address="A", phone="1", email=f"{code}@school.com", website="https://school.com"
    )


def make_user(email, role, school):
    return User.objects.create_user(email=email, password="Password123!", role=role, school=school, first_name="A", last_name="User")


class AssessmentTaskTests(APITestCase):
    def setUp(self):
        self.school_a = make_school("A")
        self.school_b = make_school("B")
        self.grade_a = Grade.objects.create(name="Grade 6", stage="primary", order=6)
        self.grade_b = Grade.objects.create(name="Grade 6", stage="primary", order=6)
        self.la_a = LearningArea.objects.create(name="Mathematics", code="MTH", grade=self.grade_a, school=self.school_a)
        self.la_b = LearningArea.objects.create(name="Mathematics", code="MTH", grade=self.grade_b, school=self.school_b)
        self.term_a = Term.objects.create(name="2026 Term 1", start_date=date(2026, 1, 1), end_date=date(2026, 6, 30), academic_year="2026", school=self.school_a)
        self.teacher_a = make_user("teacher@a.com", "TEACHER", self.school_a)
        self.student_a = make_user("student@a.com", "STUDENT", self.school_a)
        self.student_b = make_user("student@b.com", "STUDENT", self.school_b)
        self.task_a = AssessmentTask.objects.create(
            learning_area=self.la_a, term=self.term_a, title="Number Line Task",
            task_type="PPT", strand="Numbers", sub_strand="Integers", status="ACTIVE", created_by=self.teacher_a,
        )

    def test_teacher_can_create_task(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.post(
            "/api/assessment/tasks/",
            {"learning_area": self.la_a.id, "term": self.term_a.id, "title": "Fractions", "task_type": "PPT", "strand": "Fractions"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        self.assertEqual(AssessmentTask.objects.filter(title="Fractions").count(), 1)

    def test_teacher_cannot_submit_student_result(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.post(
            f"/api/assessment/tasks/{self.task_a.id}/student-result/",
            {"level_achieved": "EE", "remark": "great"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_student_can_submit_own_result(self):
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.post(
            f"/api/assessment/tasks/{self.task_a.id}/student-result/",
            {"level_achieved": "EE", "remark": "great job"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertEqual(resp.json()["level_achieved"], "EE")
        self.assertEqual(resp.json()["remark"], "great job")

    def test_student_can_read_own_result(self):
        self.client.force_authenticate(user=self.student_a)
        self.client.post(f"/api/assessment/tasks/{self.task_a.id}/student-result/", {"level_achieved": "ME", "remark": "ok"})
        resp = self.client.get(f"/api/assessment/tasks/{self.task_a.id}/student-result/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["level_achieved"], "ME")

    def test_student_cannot_access_other_school_task(self):
        self.client.force_authenticate(user=self.student_b)
        resp = self.client.get(f"/api/assessment/tasks/{self.task_a.id}/student-result/")
        self.assertEqual(resp.status_code, 404)

    def test_task_list_is_school_scoped(self):
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.get("/api/assessment/tasks/")
        data = resp.json()
        items = data["results"] if isinstance(data, dict) else data
        ids = [t["id"] for t in items]
        self.assertIn(self.task_a.id, ids)
