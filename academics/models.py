from django.db import models


class Grade(models.Model):
    STAGE_CHOICES = (
        ('pre_primary', 'Pre-Primary'),
        ('primary', 'Primary'),
        ('junior_secondary', 'Junior Secondary'),
        ('senior_secondary', 'Senior Secondary'),
    )
    name = models.CharField(max_length=50)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Pathway(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Stream(models.Model):
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='streams')
    pathway = models.ForeignKey(Pathway, null=True, blank=True, on_delete=models.SET_NULL, related_name='streams')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='streams')

    class Meta:
        ordering = ['grade__order', 'name']
        unique_together = ['school', 'grade', 'name']

    def __str__(self):
        return f'{self.grade.name} {self.name}'


class LearningArea(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='learning_areas')
    pathway = models.ForeignKey(Pathway, null=True, blank=True, on_delete=models.SET_NULL, related_name='learning_areas')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='learning_areas')

    class Meta:
        ordering = ['grade__order', 'name']
        unique_together = ['school', 'grade', 'code']

    def __str__(self):
        return f'{self.name} ({self.code})'


class Strand(models.Model):
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='strands')
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['learning_area__grade__order', 'name']

    def __str__(self):
        return f'{self.learning_area.name} - {self.name}'


class SubStrand(models.Model):
    strand = models.ForeignKey(Strand, on_delete=models.CASCADE, related_name='sub_strands')
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['strand__learning_area__grade__order', 'name']

    def __str__(self):
        return f'{self.strand} - {self.name}'


class LearningOutcome(models.Model):
    sub_strand = models.ForeignKey(SubStrand, on_delete=models.CASCADE, related_name='outcomes')
    description = models.TextField()

    class Meta:
        ordering = ['sub_strand__strand__learning_area__grade__order', 'sub_strand', 'id']

    def __str__(self):
        return self.description[:80]


class RubricDescriptor(models.Model):
    LEVEL_CHOICES = (
        ('BE', 'Below Expectation'),
        ('AE', 'Approaching Expectation'),
        ('ME', 'Meeting Expectation'),
        ('EE', 'Exceeding Expectation'),
    )
    outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name='rubric_levels')
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    descriptor_text = models.TextField()

    class Meta:
        unique_together = ['outcome', 'level']
        ordering = ['outcome__sub_strand__strand__learning_area__grade__order', 'outcome', 'level']

    def __str__(self):
        return f'{self.outcome} - {self.get_level_display()}'


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='teacher_assignments')
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='teacher_assignments')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='teacher_assignments')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='teacher_assignments')

    class Meta:
        ordering = ['stream__grade__order', 'stream__name', 'learning_area__name']
        unique_together = ['teacher', 'learning_area', 'stream']

    def __str__(self):
        return f'{self.teacher} - {self.learning_area} - {self.stream}'


class ClassTeacher(models.Model):
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='class_teachers')
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='class_teacher_assignments')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='class_teachers')
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['stream__grade__order', 'stream__name']
        unique_together = ['stream', 'teacher']

    def __str__(self):
        return f'{self.teacher} - {self.stream}'


class Enrollment(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='enrollments')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='enrollments')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['stream__grade__order', 'stream__name', 'student']
        unique_together = ['student', 'stream']

    def __str__(self):
        return f'{self.student} - {self.stream}'


class Timetable(models.Model):
    DAY_CHOICES = (
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
        ('SUNDAY', 'Sunday'),
    )
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='timetable')
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='timetable', null=True, blank=True)
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='timetable')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='timetable')

    class Meta:
        ordering = ['stream__grade__order', 'stream__name', 'day_of_week', 'start_time']

    def __str__(self):
        return f'{self.stream} - {self.learning_area} - {self.day_of_week}'


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='assignments')
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='assigned_assignments')
    due_date = models.DateTimeField(null=True, blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f'{self.title} - {self.stream} - {self.learning_area}'


class Term(models.Model):
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.CharField(max_length=20)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='terms')
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.name} ({self.academic_year})'
