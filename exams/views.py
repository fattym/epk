from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from .models import Exam, ExamGrade, ReportCard
from .serializers import ExamSerializer, ExamGradeSerializer, ReportCardSerializer
from accounts.models import ParentLearner, User
from academics.models import Term, Enrollment, Grade, LearningArea
from assessment.models import CompetencyAssessment, LearnerPortfolio
from homework.models import HomeworkSubmission


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['exam_type', 'stream', 'learning_area', 'date', 'school']

    def get_queryset(self):
        return Exam.objects.filter(school=self.request.user.school)


class ExamGradeViewSet(viewsets.ModelViewSet):
    queryset = ExamGrade.objects.all()
    serializer_class = ExamGradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'exam', 'grade', 'school']

    def get_queryset(self):
        user = self.request.user
        qs = ExamGrade.objects.filter(school=user.school)
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        if user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            return qs.filter(student_id__in=learner_ids)
        return qs


class ReportCardViewSet(viewsets.ModelViewSet):
    queryset = ReportCard.objects.all()
    serializer_class = ReportCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'stream', 'term', 'school']

    def get_queryset(self):
        user = self.request.user
        qs = ReportCard.objects.filter(school=user.school)
        if user.role == 'STUDENT':
            return qs.filter(student=user)
        if user.role == 'PARENT':
            learner_ids = ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True)
            return qs.filter(student_id__in=learner_ids)
        return qs


class CBCReportCardView(APIView):
    """Generate a consolidated CBC report card for a learner.

    Combines exam grades, competency assessment rubric levels (BE/AE/ME/EE),
    homework marks, and portfolio commentary into a single report card.

    GET /api/exams/report-cards/cbc/{student_id}/?term_id={term_id}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id=None):
        user = request.user
        term_id = request.query_params.get('term_id')

        if not student_id:
            if user.role == 'STUDENT':
                student_id = user.id
            elif user.role == 'PARENT':
                learner_ids = list(ParentLearner.objects.filter(parent=user).values_list('learner_id', flat=True))
                student_id = learner_ids[0] if learner_ids else None
            if not student_id:
                return Response({'detail': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        student_id = int(student_id)
        if user.role == 'PARENT':
            is_child = ParentLearner.objects.filter(parent=user, learner_id=student_id).exists()
            if not is_child:
                return Response({'detail': 'You can only view report cards for your own children.'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'STUDENT' and student_id != user.id:
            return Response({'detail': 'You can only view your own report card.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            student = User.objects.get(id=student_id, school=user.school)
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        enrollment = Enrollment.objects.filter(student=student, is_active=True).first()
        stream = enrollment.stream if enrollment else None
        grade = stream.grade if stream else None

        if term_id:
            try:
                term = Term.objects.get(id=term_id, school=user.school)
            except Term.DoesNotExist:
                return Response({'detail': 'Term not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            term = Term.objects.filter(is_current=True, school=user.school).first()
            if not term:
                term = Term.objects.filter(school=user.school).first()

        exam_grades = ExamGrade.objects.filter(
            student=student,
            exam__stream=stream,
            exam__learning_area__grade=grade,
            school=user.school,
        )
        if term:
            exam_grades = exam_grades.filter(exam__date__gte=term.start_date, exam__date__lte=term.end_date)

        learning_areas_map = {}
        for la in LearningArea.objects.filter(grade=grade, school=user.school):
            learning_areas_map[la.id] = {
                'id': la.id,
                'name': la.name,
                'code': la.code,
                'exams': [],
                'competency_level': None,
            }

        for eg in exam_grades.select_related('exam__learning_area', 'exam', 'graded_by'):
            la_id = eg.exam.learning_area_id
            if la_id not in learning_areas_map:
                learning_areas_map[la_id] = {
                    'id': la_id,
                    'name': eg.exam.learning_area.name,
                    'code': eg.exam.learning_area.code,
                    'exams': [],
                    'competency_level': None,
                }
            learning_areas_map[la_id]['exams'].append({
                'exam_name': eg.exam.name,
                'exam_type': eg.exam.exam_type,
                'total_marks': eg.exam.total_marks,
                'marks_obtained': eg.marks_obtained,
                'grade': eg.grade,
                'remarks': eg.remarks,
            })

        if term:
            competency = CompetencyAssessment.objects.filter(
                learner=student,
                outcome__sub_strand__strand__learning_area__grade=grade,
                term=term,
            ).select_related('outcome__sub_strand__strand__learning_area')

            la_assessments = {}
            for ca in competency:
                la_id = ca.outcome.sub_strand.strand.learning_area_id
                la_name = ca.outcome.sub_strand.strand.learning_area.name
                if la_id not in la_assessments:
                    la_assessments[la_id] = {
                        'learning_area': la_name,
                        'levels': [],
                        'comments': [],
                    }
                la_assessments[la_id]['levels'].append(ca.get_level_achieved_display())
                if ca.teacher_comment:
                    la_assessments[la_id]['comments'].append(ca.teacher_comment)

            for la_id, data in la_assessments.items():
                if la_id in learning_areas_map:
                    best_level = 'EE' if 'EE' in data['levels'] else (
                        'ME' if 'ME' in data['levels'] else (
                            'AE' if 'AE' in data['levels'] else (
                                'BE' if 'BE' in data['levels'] else None
                            )
                        )
                    )
                    level_map = {
                        'BE': 'Below Expectation',
                        'AE': 'Approaching Expectation',
                        'ME': 'Meeting Expectation',
                        'EE': 'Exceeding Expectation',
                    }
                    learning_areas_map[la_id]['competency_level'] = level_map.get(best_level, best_level)

        portfolio, _ = LearnerPortfolio.objects.get_or_create(learner=student, defaults={})

        submissions = HomeworkSubmission.objects.filter(
            student=student,
            homework__school=user.school,
        )
        if term:
            submissions = submissions.filter(homework__due_date__gte=term.start_date, homework__due_date__lte=term.end_date)

        total_marks = ExamGrade.objects.filter(
            student=student,
            exam__stream=stream,
            exam__learning_area__grade=grade,
            school=user.school,
        ).aggregate(
            total=Coalesce(Sum('exam__total_marks'), 0),
            obtained=Coalesce(Sum('marks_obtained'), 0),
        )

        obtained = total_marks['obtained']
        total = total_marks['total']
        percentage = round((obtained / total) * 100, 2) if total > 0 else 0
        grade_letter = 'A' if percentage >= 70 else ('B' if percentage >= 50 else ('C' if percentage >= 40 else 'D'))

        report_data = {
            'student': {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'email': student.email,
            },
            'stream': stream.name if stream else None,
            'grade': grade.name if grade else None,
            'term': term.name if term else None,
            'academic_year': term.academic_year if term else None,
            'period': {
                'start_date': str(term.start_date) if term else None,
                'end_date': str(term.end_date) if term else None,
            },
            'learning_areas': list(learning_areas_map.values()),
            'portfolio': {
                'current_level': portfolio.current_level,
                'strengths': portfolio.strengths,
                'areas_for_growth': portfolio.areas_for_growth,
            },
            'homework_summary': {
                'total': submissions.count(),
                'submitted': submissions.filter(status='Submitted').count() + submissions.filter(status='Late').count(),
            },
            'overall': {
                'total_marks': total,
                'obtained_marks': obtained,
                'percentage': percentage,
                'grade': grade_letter,
            },
        }

        return Response(report_data)
