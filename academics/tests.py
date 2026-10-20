
from rest_framework.test import APIClient, APITestCase

from academics.models import Grade, Stream
from accounts.models import User
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f"School {code}", code=code, address="A", phone="1", email=f"{code}@school.com", website="https://school.com"
    )


def make_user(email, role, school):
    return User.objects.create_user(email=email, password="Password123!", role=role, school=school, first_name="T", last_name="User")


class StreamRBACTests(APITestCase):
    def setUp(self):
        self.school_a = make_school("A")
        self.school_b = make_school("B")
        self.admin_a = make_user("admin@a.com", "ADMIN", self.school_a)
        self.teacher_b = make_user("teacher@b.com", "TEACHER", self.school_b)
        self.teacher_a = make_user("teacher@a.com", "TEACHER", self.school_a)
        self.student_a = make_user("student@a.com", "STUDENT", self.school_a)
        self.grade_a = Grade.objects.create(name="Grade 1", stage="primary", order=1)
        self.grade_b = Grade.objects.create(name="Grade 1", stage="primary", order=1)
        self.stream_a = Stream.objects.create(name="1A", grade=self.grade_a, school=self.school_a)
        self.stream_b = Stream.objects.create(name="1B", grade=self.grade_b, school=self.school_b)

    def test_unauthenticated_list_returns_401(self):
        client = APIClient()
        resp = client.get("/api/academics/streams/")
        self.assertEqual(resp.status_code, 401)

    def test_teacher_sees_only_own_school_streams(self):
        self.client.force_authenticate(user=self.teacher_b)
        resp = self.client.get("/api/academics/streams/")
        data = resp.json()
        items = data["results"] if isinstance(data, dict) else data
        names = [st["name"] for st in items]
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1B", names)
        self.assertNotIn("1A", names)

    def test_student_sees_only_own_school_streams(self):
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.get("/api/academics/streams/")
        data = resp.json()
        items = data["results"] if isinstance(data, dict) else data
        names = [st["name"] for st in items]
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1A", names)
        self.assertNotIn("1B", names)

    def test_admin_can_create_stream(self):
        self.client.force_authenticate(user=self.admin_a)
        resp = self.client.post(
            "/api/academics/streams/",
            {"name": "3C", "grade": self.grade_a.id, "school": self.school_a.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        self.assertTrue(Stream.objects.filter(name="3C", school=self.school_a).exists())

    def test_student_cannot_create_stream(self):
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.post(
            "/api/academics/streams/",
            {"name": "4D", "grade": self.grade_a.id, "school": self.school_a.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Stream.objects.filter(name="4D", school=self.school_a).exists())

    def test_teacher_can_create_stream(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.post(
            "/api/academics/streams/",
            {"name": "5E", "grade": self.grade_a.id, "school": self.school_a.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.json())
        self.assertTrue(Stream.objects.filter(name="5E", school=self.school_a).exists())

    def test_student_cannot_create_learning_area(self):
        la_grade = Grade.objects.create(name="Grade 1", stage="primary", order=1)
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.post(
            "/api/academics/learning-areas/",
            {"name": "Art", "code": "ART", "grade": la_grade.id, "school": self.school_a.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)


class GradeRBACTests(APITestCase):
    def setUp(self):
        self.school = make_school("GR")
        self.admin = make_user("admin@gr.com", "ADMIN", self.school)
        self.teacher = make_user("teacher@gr.com", "TEACHER", self.school)
        self.student = make_user("student@gr.com", "STUDENT", self.school)
        self.parent = make_user("parent@gr.com", "PARENT", self.school)

    def test_unauthenticated_cannot_create_grade(self):
        resp = self.client.post("/api/academics/grades/", {"name": "Test", "stage": "primary", "order": 1}, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_student_cannot_create_grade(self):
        self.client.force_authenticate(user=self.student)
        resp = self.client.post("/api/academics/grades/", {"name": "Test", "stage": "primary", "order": 1}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_parent_cannot_create_grade(self):
        self.client.force_authenticate(user=self.parent)
        resp = self.client.post("/api/academics/grades/", {"name": "Test", "stage": "primary", "order": 1}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_teacher_cannot_create_grade(self):
        self.client.force_authenticate(user=self.teacher)
        resp = self.client.post("/api/academics/grades/", {"name": "Test", "stage": "primary", "order": 1}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_create_grade(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post("/api/academics/grades/", {"name": "Test", "stage": "primary", "order": 1}, format="json")
        self.assertEqual(resp.status_code, 201, resp.json())
