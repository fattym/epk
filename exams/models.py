from django.db import models


class Exam(models.Model):
    EXAM_TYPE_CHOICES = (
        ('MIDTERM', 'Midterm'),
        ('FINAL', 'Final'),
        ('QUIZ', 'Quiz'),
        ('UNIT_TEST', 'Unit Test'),
    )
    name = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='exams')
    learning_area = models.ForeignKey('academics.LearningArea', on_delete=models.CASCADE, related_name='exams')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_marks = models.IntegerField()
    passing_marks = models.IntegerField()
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='exams')

    class Meta:
        ordering = ['-date', 'name']

    def __str__(self):
        return f'{self.name} - {self.stream}'


class ExamGrade(models.Model):
    GRADE_CHOICES = (
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    )
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='exam_grades')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    marks_obtained = models.IntegerField()
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    remarks = models.TextField(blank=True)
    graded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='graded_exams')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='grades')

    class Meta:
        ordering = ['-exam__date', 'student']

    def __str__(self):
        return f'{self.student} - {self.exam} - {self.grade}'


class ReportCard(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='report_cards')
    stream = models.ForeignKey('academics.Stream', on_delete=models.CASCADE, related_name='report_cards')
    term = models.CharField(max_length=50)
    total_marks = models.IntegerField()
    obtained_marks = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    remarks = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='report_cards')

    class Meta:
        ordering = ['-generated_at', 'student']

    def __str__(self):
        return f'{self.student} - {self.term} - {self.stream}'
