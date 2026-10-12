from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from academics.models import LearningArea, Term
from accounts.models import User, ParentLearner
from gradebook.models import LearningAreaScore, StudentBio

from .serializers import LearnerReportSerializer, compute_aggregate


def active_term(user):
    try:
        return Term.objects.filter(school=user.school).order_by("-start_date").first()
    except AttributeError:
        return Term.objects.order_by("-start_date").first()


def current_grade(student):
    enrollment = (
        student.enrollments.filter(is_active=True)
        .select_related("stream__grade")
        .first()
    )
    if not enrollment or not enrollment.stream:
        return None
    stream = enrollment.stream
    grade = getattr(stream, "grade", None)
    return f"{grade.name} {stream.name}" if grade else stream.name


def school_students_qs(user):
    """Students a given role may see in the gradebook roster (school-scoped)."""
    qs = User.objects.filter(
        role="STUDENT", school=user.school
    ).order_by("first_name", "last_name")
    if user.role == "STUDENT":
        return qs.filter(id=user.id)
    if user.role == "PARENT":
        ids = ParentLearner.objects.filter(parent=user).values_list("learner_id", flat=True)
        return qs.filter(id__in=ids)
    return qs  # TEACHER / ADMIN / STAFF / DRIVER


def can_view_report(user, learner_id):
    """A student/parent may only view their own / their wards' reports."""
    if user.role == "STUDENT":
        return learner_id == user.id
    if user.role == "PARENT":
        return ParentLearner.objects.filter(parent=user, learner_id=learner_id).exists()
    return True  # teachers/admin: school is already implied by the learner lookup


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def learner_roster(request):
    user = request.user
    qs = school_students_qs(user).select_related("student_profile")
    term = active_term(user)
    la_scores_map = {}
    for s in LearningAreaScore.objects.filter(term=term, student__in=qs).select_related("learning_area"):
        strand_avg, agg, lvl = compute_aggregate(
            s.strand1, s.strand2, s.strand3, s.csl_score
        )
        la_scores_map.setdefault(s.student_id, []).append({
            "learning_area": s.learning_area.name,
            "strands": [s.strand1, s.strand2, s.strand3],
            "csl_score": s.csl_score,
            "percentage": agg,
            "level": lvl,
            "remarks": s.remarks,
        })
    bios = {b.student_id: b for b in StudentBio.objects.filter(student__in=qs)}
    items = []
    for s in qs:
        scores = la_scores_map.get(s.id, [])
        total = sum(item["percentage"] for item in scores)
        count = len(scores)
        overall = round(total / count) if count else 0
        bio = bios.get(s.id)
        profile = getattr(s, "student_profile", None)
        items.append({
            "id": s.id,
            "name": f"{s.first_name} {s.last_name}",
            "email": s.email,
            "nemis_number": getattr(profile, "nemis_number", None),
            "assessment_number": getattr(profile, "assessment_number", None),
            "current_grade": current_grade(s),
            "sen_status": bio.get_sen_status_display() if bio else "Regular Learner",
            "parent_phone": bio.parent_phone if bio else None,
            "overall_percentage": overall,
            "la_scores": scores,
        })
    return Response({"term": term.name if term else None, "term_id": term.id if term else None, "learners": items})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def learner_report(request, pk):
    user = request.user
    learner = User.objects.filter(
        id=pk, role="STUDENT", school=user.school
    ).first()
    if not learner:
        return Response({"detail": "Learner not found."}, status=404)
    if not can_view_report(user, learner.id):
        return Response({"detail": "Not authorised to view this learner's report."}, status=403)
    term = active_term(user)
    payload = LearnerReportSerializer((learner, term)).data
    return Response(payload)


@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def update_learner_assessment(request, pk):
    """Read or patch a learner's per-learning-area straw-man strand scores (school-scoped)."""
    user = request.user
    learner = User.objects.filter(id=pk, role="STUDENT", school=user.school).first()
    if not learner:
        return Response({"detail": "Learner not found."}, status=404)

    term = active_term(user)
    if not term:
        return Response({"detail": "No active term found for your school."}, status=404)

    scores_qs = LearningAreaScore.objects.filter(
        student=learner, term=term
    ).select_related("learning_area")

    if request.method == "GET":
        return Response(
            {
                "term": term.name if term else None,
                "scores": [
                    {
                        "learning_area": s.learning_area.name,
                        "learning_area_id": s.learning_area_id,
                        "strands": [s.strand1, s.strand2, s.strand3],
                        "csl_score": s.csl_score,
                        "remarks": s.remarks,
                        "teacher_comment": s.teacher_comment,
                    }
                    for s in scores_qs
                ],
            }
        )

    la_id = request.data.get("learning_area")
    if not la_id:
        return Response({"detail": "learning_area is required."}, status=400)
    if not LearningArea.objects.filter(id=la_id, school=user.school).exists():
        return Response({"detail": "Invalid learning area for your school."}, status=400)

    allowed = {"strand1", "strand2", "strand3", "csl_score", "remarks", "teacher_comment"}
    updates = {k: request.data[k] for k in allowed if k in request.data}

    try:
        score = LearningAreaScore.objects.get(student=learner, learning_area_id=la_id, term=term)
    except LearningAreaScore.DoesNotExist:
        score = LearningAreaScore.objects.create(
            student=learner, learning_area_id=la_id, term=term
        )

    for field, value in updates.items():
        setattr(score, field, value)
    score.save()

    _, agg, level = compute_aggregate(score.strand1, score.strand2, score.strand3, score.csl_score)
    return Response(
        {
            "learning_area": score.learning_area.name,
            "strands": [score.strand1, score.strand2, score.strand3],
            "csl_score": score.csl_score,
            "remarks": score.remarks,
            "teacher_comment": score.teacher_comment,
            "percentage": agg,
            "level": level,
        }
    )
