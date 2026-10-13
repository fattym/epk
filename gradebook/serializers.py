from rest_framework import serializers

from .models import PortfolioArtifact


def compute_aggregate(strand1, strand2, strand3, csl_score):
    """Return (strand_average, aggregate_percentage, level) for a learning area.

    Mirrors the CBC formative formula used in
    cbc_gradebook_student_profile_system (2).html:
        aggregate = round((strandAvg/4)*80 + (csl/20)*20)
    """
    strand_avg = round((strand1 + strand2 + strand3) / 3, 1)
    agg = round((strand_avg / 4) * 80 + (csl_score / 20) * 20)
    return strand_avg, agg, aggregate_level(agg)


def aggregate_level(agg):
    if agg >= 80:
        return "EE"
    if agg >= 50:
        return "ME"
    return "BE"


def level_label(lvl):
    return {
        "EE": "Exceeding Expectations",
        "ME": "Meeting Expectation",
        "AE": "Approaching Expectation",
        "BE": "Below Expectation",
    }.get(lvl, lvl)


class PortfolioArtifactSerializer(serializers.ModelSerializer):
    level_label = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioArtifact
        fields = ["title", "artifact_type", "rating", "level_label", "uploaded_at"]

    def get_level_label(self, obj):
        return level_label(obj.rating)


class LearnerReportSerializer(serializers.Serializer):
    """Assembles the CBC 360 report card payload for one learner."""

    def to_representation(self, instance):
        student, term = instance if isinstance(instance, tuple) else (instance.student, None)
        from gradebook.models import (
            LearningAreaScore, StudentCompetencyScore, StudentValueScore,
            AttendanceSummary, CycleMeta,
        )

        bio = getattr(student, "gradebook_bio", None)
        profile = getattr(student, "student_profile", None)
        enrollments = student.enrollments.filter(is_active=True).select_related("stream__grade")
        enrollment = enrollments.first()
        stream = enrollment.stream if enrollment else None
        grade = stream.grade if stream else None

        current_grade = None
        if stream:
            current_grade = f"{grade.name} {stream.name}" if grade else stream.name

        # Learning-area scores present for this term
        la_scores = LearningAreaScore.objects.filter(student=student, term=term).select_related(
            "learning_area"
        ).order_by("learning_area__name")
        overall_total = 0
        overall_count = 0
        la_list = []
        for s in la_scores:
            strand_avg, agg, lvl = compute_aggregate(s.strand1, s.strand2, s.strand3, s.csl_score)
            overall_total += agg
            overall_count += 1
            la_list.append({
                "learning_area": s.learning_area.name,
                "strands": [s.strand1, s.strand2, s.strand3],
                "strand_average": strand_avg,
                "csl_score": s.csl_score,
                "overall_level": lvl,
                "overall_label": level_label(lvl),
                "percentage": agg,
                "remarks": s.remarks,
            })

        overall_agg = round(overall_total / overall_count) if overall_count else 0
        overall_lvl = aggregate_level(overall_agg)

        competencies = [
            {"competency": c.competency.name, "score": c.score}
            for c in StudentCompetencyScore.objects.filter(student=student, term=term)
            .select_related("competency")
            .order_by("competency__order")
        ]
        values = [
            {
                "value": v.value.name,
                "level": v.level,
                "level_label": level_label(v.level),
            }
            for v in StudentValueScore.objects.filter(student=student, term=term)
            .select_related("value")
            .order_by("value__order")
        ]
        artifacts = PortfolioArtifactSerializer(
            PortfolioArtifact.objects.filter(student=student, term=term)
            .order_by("-uploaded_at")[:6],
            many=True,
        ).data

        return {
            "student": {
                "id": student.id,
                "name": f"{student.first_name} {student.last_name}",
                "email": student.email,
                "nemis_number": getattr(profile, "nemis_number", None),
                "assessment_number": getattr(profile, "assessment_number", None),
                "admission_number": getattr(profile, "admission_number", None),
                "current_grade": current_grade,
                "date_of_birth": bio.date_of_birth if bio else None,
                "parent_phone": bio.parent_phone if bio else None,
                "sen_status": bio.get_sen_status_display() if bio else "Regular Learner",
            },
            "term": {
                "id": term.id,
                "name": term.name,
                "academic_year": term.academic_year,
                "start_date": term.start_date,
                "end_date": term.end_date,
            },
            "school_info": {
                "name": school_name(student, term),
                "address": school_address(student),
                "email": school_email(student),
                "code": school_code(student),
            },
            "homeroom_teacher": homeroom_teacher(term),
            "attendance": attendance_summary(student, term),
            "learning_area_scores": la_list,
            "overall": {
                "percentage": overall_agg,
                "level": overall_lvl,
                "label": level_label(overall_lvl),
            },
            "core_competencies": competencies,
            "core_values": values,
            "portfolio_artifacts": artifacts,
        }


def school_name(student, term):
    school = getattr(term, "school", None) or getattr(student, "school", None)
    return getattr(school, "name", None) or "Nairobi STEM Academy"


def school_address(student):
    school = getattr(student, "school", None)
    return getattr(school, "address", None) or "P.O. Box 40100-00100, Nairobi"


def school_email(student):
    school = getattr(student, "school", None)
    return getattr(school, "email", None) or "info@school.ac.ke"


def school_code(student):
    school = getattr(student, "school", None)
    return getattr(school, "code", None) or "20401123"


def homeroom_teacher(term):
    cm = getattr(term, "cycle_meta", None)
    return cm.homeroom_teacher if cm else "Mr. J. Mwangi"


def attendance_summary(student, term):
    att = student.gradebook_attendance_summaries.filter(term=term).first()
    if not att:
        return {"days_present": 0, "days_total": 0, "percentage": 0}
    return {
        "days_present": att.days_present,
        "days_total": att.days_total,
        "percentage": att.percentage,
    }
