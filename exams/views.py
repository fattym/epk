from rest_framework import viewsets, permissions, status
from .models import Exam, ExamGrade, ReportCard
from .serializers import ExamSerializer, ExamGradeSerializer, ReportCardSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'exam', 'grade', 'school']

    def get_queryset(self):
        return ExamGrade.objects.filter(school=self.request.user.school)

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
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'stream', 'term', 'school']

    def get_queryset(self):
        return ReportCard.objects.filter(school=self.request.user.school)