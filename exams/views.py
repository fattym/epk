from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum, Count, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from .models import Exam, ExamGrade, ReportCard
from .serializers import ExamSerializer, ExamGradeSerializer, ReportCardSerializer
from accounts.models import ParentLearner, User
from accounts.permissions import IsAdminOrStaffOrTeacher
from academics.models import Term, Enrollment, Grade, LearningArea
from assessment.models import CompetencyAssessment, LearnerPortfolio
from homework.models import HomeworkSubmission


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
    filterset_fields = ['exam_type', 'stream', 'learning_area', 'date', 'school']
    
    def get_queryset(self):
        return Exam.objects.filter(school=self.request.user.school)

    @action(detail=True, methods=['get'], url_path='result-summary')
    def result_summary(self, request, pk=None):
        """Get exam result summary including statistics and toppers."""
        exam = self.get_object()
        
        # Get all marks for this exam
        marks = ExamGrade.objects.filter(exam=exam)
        total_students = marks.count()
        
        if total_students == 0:
            return Response({
                'total_students': 0,
                'top_score': 0,
                'average_score': 0,
                'passed_count': 0,
                'failed_count': 0,
                'top_students': []
            })
        
        # Calculate statistics
        marks_list = list(marks.values_list('marks_obtained', flat=True))
        top_score = max(marks_list) if marks_list else 0
        average_score = sum(marks_list) / total_students if marks_list else 0
        passed_count = sum(1 for m in marks_list if m >= exam.passing_marks)
        failed_count = total_students - passed_count
        
        # Get toppers (top 10 students)
        toppers = ExamGrade.objects.filter(exam=exam).order_by('-marks_obtained')[:10]
        top_students = [
            {
                'student_id': mark.student_id,
                'student_name': f"{mark.student.first_name} {mark.student.last_name}",
                'marks': mark.marks_obtained,
                'grade': mark.grade
            } for mark in toppers
        ]
        
        return Response({
            'exam_id': exam.id,
            'exam_name': exam.name,
            'total_students': total_students,
            'top_score': top_score,
            'average_score': round(average_score, 2),
            'passed_count': passed_count,
            'failed_count': failed_count,
            'top_students': top_students
        })
    
    @action(detail=False, methods=['get'], url_path='toppers')
    def toppers(self, request):
        """Get toppers list for the school."""
        exams = Exam.objects.filter(school=self.request.user.school).order_by('-date')[:5]
        all_toppers = []
        
        for exam in exams:
            top_marks = ExamGrade.objects.filter(exam=exam).order_by('-marks_obtained')[:10]
            for mark in top_marks:
                all_toppers.append({
                    'student_id': mark.student_id,
                    'student_name': f"{mark.student.first_name} {mark.student.last_name}",
                    'marks': mark.marks_obtained,
                    'grade': mark.grade,
                    'exam': exam.name
                })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_toppers = []
        for topper in all_toppers:
            key = (topper['student_id'], topper['exam'])
            if key not in seen:
                seen.add(key)
                unique_toppers.append(topper)
        
        return Response({
            'school': self.request.user.school.name,
            'toppers': unique_toppers[:10]
        })


class ExamGradeViewSet(viewsets.ModelViewSet):
    queryset = ExamGrade.objects.all()
    serializer_class = ExamGradeSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
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

    @action(detail=False, methods=['post'], url_path='bulk-enter')
    def bulk_enter(self, request):
        """Bulk enter marks for an exam."""
        exam_id = request.data.get('exam_id')
        marks_data = request.data.get('marks_data', [])
        
        if not exam_id or not isinstance(marks_data, list):
            return Response(
                {'detail': 'exam_id and marks_data are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exam = Exam.objects.get(id=exam_id, school=request.user.school)
        except Exam.DoesNotExist:
            return Response({'detail': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
        
        results = []
        errors = []
        
        for i, mark_data in enumerate(marks_data):
            try:
                student_id = mark_data.get('student_id')
                marks = mark_data.get('marks')
                out_of_marks = mark_data.get('out_of_marks')
                remarks = mark_data.get('remarks', '')
                
                if not all([student_id, marks is not None, out_of_marks]):
                    errors.append({
                        'index': i,
                        'error': 'student_id, marks, and out_of_marks are required'
                    })
                    continue
                
                # Calculate percentage
                percentage = round((marks / out_of_marks * 100), 2) if out_of_marks else 0
                
                # Get student
                try:
                    student = User.objects.get(id=student_id, school=request.user.school)
                except User.DoesNotExist:
                    errors.append({
                        'index': i,
                        'error': f'Student {student_id} not found'
                    })
                    continue
                
                # Create or update mark
                mark, created = ExamGrade.objects.get_or_create(
                    student=student,
                    exam=exam,
                    school=request.user.school,
                    defaults={
                        'marks_obtained': marks,
                        'grade': '',
                        'remarks': remarks,
                        'graded_by': request.user,
                    }
                )
                
                if not created:
                    mark.marks_obtained = marks
                    mark.grade = ''
                    mark.remarks = remarks
                    mark.graded_by = request.user
                    mark.save()
                
                results.append({
                    'student_id': student_id,
                    'student_name': f"{student.first_name} {student.last_name}",
                    'marks': marks,
                    'percentage': percentage,
                    'created': created
                })
                
            except Exception as e:
                errors.append({
                    'index': i,
                    'error': str(e)
                })
        
        return Response({
            'message': 'Marks entered successfully',
            'entered': len(results),
            'errors': errors
        }, status=status.HTTP_200_OK)


class ReportCardViewSet(viewsets.ModelViewSet):
    queryset = ReportCard.objects.all()
    serializer_class = ReportCardSerializer
    permission_classes = [IsAdminOrStaffOrTeacher]
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
