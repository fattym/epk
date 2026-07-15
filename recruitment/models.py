from django.db import models


class PipelineStage(models.Model):
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='pipeline_stages')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['school', 'name']

    def __str__(self):
        return f'{self.school.name} - {self.name}'


class JobPosting(models.Model):
    EMPLOYMENT_TYPE_CHOICES = (
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
    )
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    department = models.CharField(max_length=100, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='FULL_TIME')
    location = models.CharField(max_length=255, blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    posted_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='job_postings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.school.name} - {self.title}'


class Candidate(models.Model):
    SOURCE_CHOICES = (
        ('REFERRAL', 'Employee Referral'),
        ('LINKEDIN', 'LinkedIn'),
        ('WEBSITE', 'School Website'),
        ('OTHER', 'Other'),
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(upload_to='recruitment/resumes/%Y/%m/')
    cover_letter = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='WEBSITE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['email']

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}>'


class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('SCREENING', 'Screening'),
        ('INTERVIEW', 'Interview'),
        ('OFFERED', 'Offered'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['job_posting', 'candidate']

    def __str__(self):
        return f'{self.candidate} -> {self.job_posting}'


class Interview(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(max_length=255, blank=True)
    video_link = models.URLField(blank=True)
    interviewers = models.ManyToManyField('accounts.User', related_name='interviews')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_interviews')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'Interview - {self.application}'


class ScoreCard(models.Model):
    RECOMMENDATION_CHOICES = (
        ('STRONG_HIRE', 'Strong Hire'),
        ('HIRE', 'Hire'),
        ('NO_DECISION', 'No Decision'),
        ('NO_HIRE', 'No Hire'),
        ('STRONG_NO_HIRE', 'Strong No Hire'),
    )
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='score_cards')
    interviewer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='score_cards')
    rating = models.PositiveSmallIntegerField()
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    strengths = models.TextField(blank=True)
    concerns = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['interview', 'interviewer']

    def __str__(self):
        return f'ScoreCard - {self.interview} - {self.interviewer}'


class Offer(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('EXPIRED', 'Expired'),
    )
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='offer')
    position = models.CharField(max_length=255)
    salary_offered = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_offers')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Offer - {self.application}'
