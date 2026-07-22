from django.db import models
from django.utils import timezone
from accounts.models import User
from academics.models import LearningArea, SubStrand, Stream, Grade, Term
from tenants.models import School


class Course(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted_for_review', 'Submitted for Review'),
        ('published', 'Published'),
    )
    DELIVERY_MODE_CHOICES = (
        ('teacher_led', 'Teacher Led'),
        ('self_paced', 'Self Paced'),
        ('blended', 'Blended'),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='courses')
    learning_area = models.ForeignKey(LearningArea, on_delete=models.CASCADE, related_name='courses')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_courses')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taught_courses')

    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    year = models.CharField(max_length=10, blank=True, help_text="Academic year, e.g. 2026")

    title = models.CharField(max_length=255, blank=True, default='Untitled Course')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODE_CHOICES, default='blended')

    available_from = models.DateTimeField(null=True, blank=True)
    requires_parent_unlock = models.BooleanField(default=False)

    section = models.CharField(max_length=50, blank=True, help_text="e.g. Section A, Group 1")
    room = models.CharField(max_length=100, blank=True, help_text="Physical room or virtual link")
    course_code = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="Short code for students to join")
    allow_student_posts = models.BooleanField(default=False, help_text="Allow students to post in the class stream")
    core_competencies = models.JSONField(default=list, blank=True)
    values = models.JSONField(default=list, blank=True)
    pcis = models.JSONField(default=list, blank=True)

    cloned_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='clones')
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        parts = []
        if self.grade and self.stream:
            parts.append(f"{self.grade.name}{self.stream.name}")
        elif self.stream:
            parts.append(str(self.stream))
        if self.learning_area:
            parts.append(self.learning_area.name)
        if self.term:
            parts.append(self.term.name)
        return " - ".join(parts) if parts else f"{self.title} (v{self.version})"

    def save(self, *args, **kwargs):
        if not self.course_code:
            import random, string
            self.course_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        super().save(*args, **kwargs)


class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics', null=True, blank=True)
    scheme_entry = models.ForeignKey('curriculum.SchemeWeek', on_delete=models.SET_NULL, null=True, blank=True, related_name='topics')
    title = models.CharField(max_length=255)
    week = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    learning_area = models.ForeignKey(LearningArea, on_delete=models.SET_NULL, null=True, blank=True, related_name='topics')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='topics')
    sub_strand = models.ForeignKey(SubStrand, on_delete=models.SET_NULL, null=True, blank=True, related_name='topics')
    learning_outcomes = models.TextField(blank=True, help_text="Objectives copied from the scheme of work")

    class Meta:
        ordering = ['course', 'week', 'order']

    def __str__(self):
        return f"{self.course} - {self.title}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    sub_strand = models.ForeignKey(SubStrand, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255, blank=True)
    lesson_number = models.PositiveIntegerField(default=1)
    strand = models.CharField(max_length=255, blank=True, help_text="Strand / Topic")
    objectives = models.TextField(blank=True)
    learning_activities = models.TextField(blank=True)
    resources = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, max_length=500)
    attachment = models.FileField(upload_to='course_attachments/%Y/%m/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    prerequisite = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependents')
    is_published = models.BooleanField(default=False)
    publish_at = models.DateTimeField(null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='lessons')

    class Meta:
        ordering = ['order', 'lesson_number']

    def __str__(self):
        return f"{self.lesson_number}. {self.title or self.strand or 'Lesson'} ({self.sub_strand.name})"

    @property
    def is_visible(self):
        if not self.is_published:
            return False
        if self.publish_at and self.publish_at > timezone.now():
            return False
        return True


class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='course_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['course', 'learner']


class LessonProgress(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    is_completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    marked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='marked_lessons')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='lesson_progress')

    class Meta:
        unique_together = ['lesson', 'learner']


class LearningMaterial(models.Model):
    TYPE_CHOICES = (
        ('video', 'Video'),
        ('pdf', 'PDF / Notes'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')
    material_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='pdf')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, help_text="Notes text or assignment description")
    file = models.FileField(upload_to='course_materials/%Y/%m/', blank=True, null=True)
    url = models.URLField(blank=True, max_length=500, help_text="Video or external link")
    order = models.PositiveIntegerField(default=0)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='learning_materials')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.get_material_type_display()}: {self.title}"


class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='quizzes')

    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    correct = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    taken_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='quiz_attempts')

    class Meta:
        ordering = ['-taken_at']


class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='course_comments')

    class Meta:
        ordering = ['created_at']


class Post(models.Model):
    TYPE_CHOICES = (
        ('assignment', 'Assignment'),
        ('material', 'Material'),
        ('question', 'Question'),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='posts')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_posts')
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='material')
    title = models.CharField(max_length=255, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='posts')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_post_type_display()} - {self.course}"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='post_comments')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user} on {self.post}"


class Assignment(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='assignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    instructions = models.TextField()
    due_date = models.DateTimeField(null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='course_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.course}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    answer = models.TextField(blank=True)
    file = models.FileField(upload_to='submissions/%Y/%m/', blank=True, null=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='submissions')

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student} - {self.assignment}"
