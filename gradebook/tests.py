from datetime import date

from rest_framework.test import APITestCase

from academics.models import Enrollment, Grade, LearningArea, Stream, Term
from accounts.models import User
from gradebook.models import LearningAreaScore
from gradebook.serializers import compute_aggregate
from tenants.models import School


def make_school(code):
    return School.objects.create(
        name=f"School {code}", code=code, address="A", phone="1", email=f"{code}@school.com", website="https://school.com"
    )


def make_user(email, role, school):
    return User.objects.create_user(email=email, password="Password123!", role=role, school=school, first_name="A", last_name="User")


class ComputeAggregateTests(APITestCase):
    def test_ee_boundary(self):
        _, agg, level = compute_aggregate(3, 3, 4, 16)
        self.assertEqual(agg, 83)
        self.assertEqual(level, "EE")

    def test_me_boundary(self):
        _, agg, level = compute_aggregate(3, 3, 4, 11)
        self.assertEqual(agg, 78)
        self.assertEqual(level, "ME")

    def test_be_below_me(self):
        _, agg, level = compute_aggregate(2, 2, 2, 9)
        self.assertEqual(agg, 49)
        self.assertEqual(level, "BE")


class LearnerRosterTests(APITestCase):
    def setUp(self):
        self.school_a = make_school("A")
        self.school_b = make_school("B")
        self.grade = Grade.objects.create(name="Grade 1", stage="primary", order=1)
        self.stream = Stream.objects.create(name="1A", grade=self.grade, school=self.school_a)
        self.term = Term.objects.create(name="2026 Term 1", start_date=date(2026, 1, 1), end_date=date(2026, 6, 30), academic_year="2026", school=self.school_a)
        self.la = LearningArea.objects.create(name="Mathematics", code="MTH", grade=self.grade, school=self.school_a)
        self.student_a = make_user("student@a.com", "STUDENT", self.school_a)
        self.student_b = make_user("student@b.com", "STUDENT", self.school_b)
        self.teacher_a = make_user("teacher@a.com", "TEACHER", self.school_a)
        self.teacher_b = make_user("teacher@b.com", "TEACHER", self.school_b)
        Enrollment.objects.create(student=self.student_a, stream=self.stream, school=self.school_a)
        LearningAreaScore.objects.create(student=self.student_a, learning_area=self.la, term=self.term, strand1=3, strand2=3, strand3=4, csl_score=16)

    def test_roster_is_school_scoped(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.get("/api/gradebook/learners/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        names = [lr["name"] for lr in data["learners"]]
        self.assertIn("A User", names)
        self.assertNotIn("User", names)

    def test_student_sees_only_self(self):
        self.client.force_authenticate(user=self.student_a)
        resp = self.client.get("/api/gradebook/learners/")
        self.assertEqual(resp.status_code, 200)
        names = [lr["name"] for lr in resp.json()["learners"]]
        self.assertEqual(names, ["A User"])

    def test_aggregate_values_in_roster(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.get("/api/gradebook/learners/")
        learner = next(lr for lr in resp.json()["learners"] if lr["name"] == "A User")
        self.assertEqual(learner["current_grade"], "Grade 1 1A")
        score = learner["la_scores"][0]
        self.assertEqual(score["percentage"], 83)
        self.assertEqual(score["level"], "EE")

    def test_patch_recomputes_aggregate(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.patch(
            f"/api/gradebook/learners/{self.student_a.id}/assessments/",
            {"learning_area": self.la.id, "csl_score": 11},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.json())
        body = resp.json()
        self.assertEqual(body["percentage"], 78)
        self.assertEqual(body["level"], "ME")

    def test_patch_accepts_stringified_numbers(self):
        self.client.force_authenticate(user=self.teacher_a)
        resp = self.client.patch(
            f"/api/gradebook/learners/{self.student_a.id}/assessments/",
            {"learning_area": self.la.id, "csl_score": "11"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertEqual(resp.json()["percentage"], 78)

    def test_other_school_teacher_cannot_see_roster(self):
        self.client.force_authenticate(user=self.teacher_b)
        resp = self.client.get("/api/gradebook/learners/")
        learner_ids = [lr["id"] for lr in resp.json()["learners"]]
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.student_b.id, learner_ids)
        self.assertNotIn(self.student_a.id, learner_ids)
