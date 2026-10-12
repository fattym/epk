import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import Grade, Stream, LearningArea, Term, Enrollment
from accounts.models import User, StudentProfile
from gradebook.models import (
    CoreCompetency,
    CoreValue,
    StudentBio,
    LearningAreaScore,
    StudentCompetencyScore,
    StudentValueScore,
    PortfolioArtifact,
    AttendanceSummary,
    CycleMeta,
)

SCHOOL_CODE = "NSA-001"

# 7 CBC core competencies
COMPETENCIES = [
    ("COMM", "Communication"),
    ("CTPS", "Critical Thinking & Problem Solving"),
    ("CI", "Creativity & Imagination"),
    ("CIV", "Citizenship"),
    ("DLIT", "Digital Literacy"),
    ("L2L", "Learning to Learn"),
    ("SE", "Self-Efficacy"),
]

# 4 core values
VALUES = [
    ("INTEGRITY", "Integrity & Honesty"),
    ("RESPECT", "Respect & Courtesy"),
    ("RESPONSIBILITY", "Responsibility & Leadership"),
    ("PATRIOTISM", "Patriotism & Community"),
]

# Template learners from cbc_gradebook_student_profile_system (2).html
LEARNERS = [
    {
        "first_name": "Amina", "last_name": "Kiprono",
        "email": "amina.kiprono@school.ac.ke",
        "nemis": "MZX-9821-2024", "knec": "20401123004", "adm": "ADM/001/2026",
        "dob": datetime.date(2013, 5, 14), "parent_phone": "0722-123-456",
        "sen": "REG",
        "scores": {
            "Integrated Science": {"strands": [4, 4, 3], "csl": 18,
                                   "remarks": "Demonstrates outstanding leadership in group science projects.",
                                   "comment": "Strong inquiry skills; exceeds CBC benchmarks."},
            "Mathematics": {"strands": [4, 3, 4], "csl": 17,
                            "remarks": "Strong problem solving ability in numeric strands.",
                            "comment": "Consistently applies logical reasoning."},
            "Social Studies & CSL": {"strands": [3, 3, 3], "csl": 18,
                                     "remarks": "Active participation in community environment activities.",
                                     "comment": "Shows civic responsibility."},
        },
        "competencies": [90, 85, 95, 80, 88, 92, 84],
        "values": {"INTEGRITY": "EE", "RESPECT": "EE", "RESPONSIBILITY": "ME", "PATRIOTISM": "EE"},
    },
    {
        "first_name": "David", "last_name": "Njoroge",
        "email": "david.njoroge@school.ac.ke",
        "nemis": "MZX-4410-2024", "knec": "20401123008", "adm": "ADM/002/2026",
        "dob": datetime.date(2013, 8, 22), "parent_phone": "0733-987-654",
        "sen": "REG",
        "scores": {
            "Integrated Science": {"strands": [3, 3, 2], "csl": 14,
                                   "remarks": "Good progress in practicals; requires mild encouragement in energy calculations.",
                                   "comment": "Making steady progress."},
            "Mathematics": {"strands": [3, 3, 3], "csl": 16,
                            "remarks": "Solid understanding; keep practicing word problems.",
                            "comment": "Meeting expectations."},
            "Social Studies & CSL": {"strands": [3, 3, 2], "csl": 15,
                                     "remarks": "Participates well; deepen analysis of case studies.",
                                     "comment": "Developing analytical skills."},
        },
        "competencies": [70, 75, 68, 72, 80, 65, 78],
        "values": {"INTEGRITY": "ME", "RESPECT": "ME", "RESPONSIBILITY": "ME", "PATRIOTISM": "AE"},
    },
    {
        "first_name": "Faith", "last_name": "Cherono",
        "email": "faith.cherono@school.ac.ke",
        "nemis": "MZX-7729-2024", "knec": "20401123012", "adm": "ADM/003/2026",
        "dob": datetime.date(2013, 3, 10), "parent_phone": "0711-555-222",
        "sen": "GAT",
        "scores": {
            "Integrated Science": {"strands": [4, 4, 4], "csl": 20,
                                   "remarks": "Exceptional mastery of all environmental concepts and scientific inquiry.",
                                   "comment": "Advanced reasoning; ready for extension."},
            "Mathematics": {"strands": [4, 4, 4], "csl": 20,
                            "remarks": "Masterful problem solving and concept transfer.",
                            "comment": "Exceeds CBC expectations."},
            "Social Studies & CSL": {"strands": [4, 4, 4], "csl": 20,
                                     "remarks": "Exceptional grasp of civic concepts and community engagement.",
                                     "comment": "Outstanding leadership."},
        },
        "competencies": [98, 92, 96, 95, 90, 94, 96],
        "values": {"INTEGRITY": "EE", "RESPECT": "EE", "RESPONSIBILITY": "EE", "PATRIOTISM": "EE"},
    },
    {
        "first_name": "Kevin", "last_name": "Wafula",
        "email": "kevin.wafula@school.ac.ke",
        "nemis": "MZX-1102-2024", "knec": "20401123019", "adm": "ADM/004/2026",
        "dob": datetime.date(2013, 11, 5), "parent_phone": "0700-112-334",
        "sen": "REMEDIAL",
        "scores": {
            "Integrated Science": {"strands": [2, 1, 2], "csl": 10,
                                   "remarks": "Requires targeted intervention in Strand 2 vocabulary and task completion.",
                                   "comment": "Needs structured support."},
            "Mathematics": {"strands": [2, 1, 2], "csl": 11,
                            "remarks": "Struggles with foundational concepts; build confidence.",
                            "comment": "Needs remediation."},
            "Social Studies & CSL": {"strands": [1, 1, 2], "csl": 9,
                                     "remarks": "Requires scaffolding to access content.",
                                     "comment": "Low engagement."},
        },
        "competencies": [52, 48, 55, 60, 45, 50, 58],
        "values": {"INTEGRITY": "AE", "RESPECT": "ME", "RESPONSIBILITY": "BE", "PATRIOTISM": "AE"},
    },
]


class Command(BaseCommand):
    help = "Seed CBC gradebook demo data to match cbc_gradebook_student_profile_system (2).html"

    def handle(self, *args, **options):
        from tenants.models import School

        try:
            school = School.objects.get(code=SCHOOL_CODE)
        except School.DoesNotExist:
            self.stderr.write(f"School code {SCHOOL_CODE} not found.")
            return

        with transaction.atomic():
            # Master data
            for i, (code, name) in enumerate(COMPETENCIES):
                CoreCompetency.objects.get_or_create(code=code, defaults={"name": name, "order": i + 1})
            for i, (code, name) in enumerate(VALUES):
                CoreValue.objects.get_or_create(code=code, defaults={"name": name, "order": i + 1})

            # Grade 6 + stream "East"
            grade6 = Grade.objects.filter(name="Grade 6").first()
            if not grade6:
                grade6 = Grade.objects.create(name="Grade 6", stage="primary", order=8)
            stream, _ = Stream.objects.get_or_create(
                school=school, grade=grade6, name="East",
            )

            # Grade 6 learning areas matching the report card rows
            la_map = {}
            for code, name in [
                ("SCI", "Integrated Science"),
                ("MAT", "Mathematics"),
                ("SST", "Social Studies & CSL"),
            ]:
                la, _ = LearningArea.objects.get_or_create(
                    school=school, grade=grade6, code=code,
                    defaults={"name": name, "pathway": None},
                )
                # ensure name matches template exactly
                if la.name != name:
                    la.name = name
                    la.save(update_fields=["name"])
                la_map[name] = la

            # Term: 2026 Term 1
            term, _ = Term.objects.get_or_create(
                school=school, name="2026 Term 1",
                defaults={
                    "start_date": datetime.date(2026, 1, 6),
                    "end_date": datetime.date(2026, 4, 10),
                    "academic_year": "2025-2026",
                    "is_current": True,
                },
            )
            term.is_current = True
            term.save(update_fields=["is_current"])

            # Class teacher for the active cycle
            CycleMeta.objects.update_or_create(term=term, defaults={"homeroom_teacher": "Mr. J. Mwangi"})

            comp_by_code = {c.code: c for c in CoreCompetency.objects.all()}
            val_by_code = {c.code: c for c in CoreValue.objects.all()}

            artifacts = [
                ("Soil Science Lab Report", "document", "EE", datetime.date(2026, 2, 12)),
                ("Tree Planting CSL Photo", "image", "EE", datetime.date(2026, 3, 4)),
                ("Robotics & Coding Project", "document", "EE", datetime.date(2026, 3, 18)),
            ]

            for spec in LEARNERS:
                user = User.objects.filter(email=spec["email"], school=school).first()
                if not user:
                    user = User.objects.create_user(
                        email=spec["email"],
                        password="Learner@1234",
                        first_name=spec["first_name"],
                        last_name=spec["last_name"],
                        role="STUDENT",
                        school=school,
                        date_of_birth=spec["dob"],
                        phone=spec["parent_phone"],
                    )
                else:
                    user.first_name = spec["first_name"]
                    user.last_name = spec["last_name"]
                    user.role = "STUDENT"
                    user.date_of_birth = spec["dob"]
                    user.phone = spec["parent_phone"]
                    user.is_active = True
                    user.set_password("Learner@1234")
                    user.save(update_fields=["first_name", "last_name", "role", "date_of_birth", "phone", "is_active", "password"])

                # StudentProfile (NEMIS / KNEC / Admn)
                profile, _ = StudentProfile.objects.get_or_create(
                    user=user, defaults={"school": school}
                )
                profile.nemis_number = spec["nemis"]
                profile.assessment_number = spec["knec"]
                profile.admission_number = spec["adm"]
                profile.save(update_fields=["nemis_number", "assessment_number", "admission_number"])

                # Enrollment (active)
                Enrollment.objects.get_or_create(
                    student=user, stream=stream, school=school,
                    defaults={"is_active": True},
                )

                # StudentBio (SEN + parent phone + DOB)
                bio, _ = StudentBio.objects.get_or_create(student=user)
                bio.sen_status = spec["sen"]
                bio.parent_phone = spec["parent_phone"]
                bio.date_of_birth = spec["dob"]
                bio.save(update_fields=["sen_status", "parent_phone", "date_of_birth"])

                # Attendance summary (matches template: 64 / 65 days present)
                AttendanceSummary.objects.update_or_create(
                    student=user, term=term,
                    defaults={"days_present": 64, "days_total": 65},
                )

                # Learning area scores
                for la_name, data in spec["scores"].items():
                    la = la_map[la_name]
                    LearningAreaScore.objects.update_or_create(
                        student=user, learning_area=la, term=term,
                        defaults={
                            "strand1": data["strands"][0],
                            "strand2": data["strands"][1],
                            "strand3": data["strands"][2],
                            "csl_score": data["csl"],
                            "remarks": data["remarks"],
                            "teacher_comment": data["comment"],
                        },
                    )

                # Core competency scores
                for (code, comp), score in zip(COMPETENCIES, spec["competencies"]):
                    StudentCompetencyScore.objects.update_or_create(
                        student=user, competency=comp_by_code[code], term=term,
                        defaults={"score": score},
                    )

                # Core value scores
                for code, level in spec["values"].items():
                    StudentValueScore.objects.update_or_create(
                        student=user, value=val_by_code[code], term=term,
                        defaults={"level": level},
                    )

                # Portfolio artifacts (only Amina gets artifacts per template)
                if spec["first_name"] == "Amina":
                    for title, atype, rating, uploaded in artifacts:
                        PortfolioArtifact.objects.update_or_create(
                            student=user, term=term, title=title,
                            defaults={
                                "artifact_type": atype,
                                "rating": rating,
                                "uploaded_at": uploaded,
                            },
                        )

                self.stdout.write(self.style.SUCCESS(f"Seeded {user} with full gradebook data."))

            # --- Teacher + assessment tasks (feeds the CBC teacher dashboard) ---
            from academics.models import Strand, SubStrand, LearningOutcome
            from assessment.models import CompetencyAssessment as CA

            teacher, _ = User.objects.get_or_create(
                email="agnes.mutua@school.ac.ke",
                defaults={
                    "password": "Teacher@1234",
                    "first_name": "Agnes",
                    "last_name": "Mutua",
                    "role": "TEACHER",
                    "school": school,
                    "is_active": True,
                },
            )
            if not User.objects.filter(email="agnes.mutua@school.ac.ke").first().has_usable_password():
                teacher.set_password("Teacher@1234")
                teacher.save(update_fields=["password"])

            # Strands + sub-strands + learning outcomes for the Grade 6 learning areas
            strands_cfg = {
                "Integrated Science": [
                    ("Human Body Systems", ["Digestion", "Respiratory System"]),
                    ("Environmental Studies", ["Ecosystems", "Weather & Climate"]),
                ],
                "Mathematics": [
                    ("Numbers & Operations", ["Whole Numbers", "Fractions"]),
                    ("Geometry", ["Lines & Angles", "Area"]),
                ],
                "Social Studies & CSL": [
                    ("Community & Citizenship", ["Family Roles", "Map Reading"]),
                    ("Environment & Population", ["Weather", "Population"]),
                ],
            }
            outcome_map = {}  # (la_name, strand_name) -> first outcome
            for la_name, strands in strands_cfg.items():
                la = la_map[la_name]
                for strand_name, sub_names in strands:
                    strand = Strand.objects.get_or_create(learning_area=la, name=strand_name)[0]
                    for sub_name in sub_names:
                        sub = SubStrand.objects.get_or_create(strand=strand, name=sub_name)[0]
                        desc = f"{sub_name} learning outcomes"
                        outcome = LearningOutcome.objects.get_or_create(
                            sub_strand=sub,
                            description=desc,
                        )[0]
                        outcome_map[(la_name, strand_name)] = outcome

            # 6 sample competency assessments across learners, spread across LAs/sub-strands
            tasks = [
                ("Amina Kiprono", "Integrated Science", "Human Body Systems", "EE",
                 "Outstanding practical demonstration of the digestive process."),
                ("David Njoroge", "Integrated Science", "Human Body Systems", "ME",
                 "Good description; needs more detail on enzymes."),
                ("Faith Cherono", "Mathematics", "Numbers & Operations", "EE",
                 "Exceptional fluency with whole-number operations."),
                ("Kevin Wafula", "Mathematics", "Numbers & Operations", "BE",
                 "Requires re-teaching of place value concepts."),
                ("Amina Kiprono", "Social Studies & CSL", "Community & Citizenship", "EE",
                 "Shows excellent civic responsibility in group work."),
                ("Faith Cherono", "Social Studies & CSL", "Environment & Population", "EE",
                 "Exceptional analysis of weather patterns."),
            ]
            for name, la_name, strand_name, level, comment in tasks:
                first, last = name.split(" ")
                learner_user = User.objects.filter(first_name=first, last_name=last, school=school).first()
                if not learner_user:
                    continue
                outcome = outcome_map.get((la_name, strand_name))
                if not outcome:
                    continue
                CA.objects.update_or_create(
                    learner=learner_user, outcome=outcome, term=term,
                    defaults={
                        "assessed_by": teacher,
                        "level_achieved": level,
                        "teacher_comment": comment,
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"  task: {name} - {la_name}/{strand_name} {level}"))

        self.stdout.write(self.style.SUCCESS("Gradebook demo data seeded."))
