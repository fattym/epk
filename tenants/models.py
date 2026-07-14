from django.db import models


class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='schools/logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolSettings(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='settings')
    academic_year = models.CharField(max_length=20)
    current_term = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    allow_parent_portal = models.BooleanField(default=True)
    allow_student_portal = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.school.name} Settings'
