from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
        ('STAFF', 'Staff'),
        ('DISTRIBUTOR', 'Distributor'),
    )
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, null=True, blank=True)
    # TSC (Teachers Service Commission) compliance — captured now, not retrofitted.
    tsc_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    qualification = models.CharField(max_length=200, blank=True)
    subject_specializations = models.ManyToManyField(
        'academics.LearningArea', related_name='specialist_teachers', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class ParentLearner(models.Model):
    parent = models.ForeignKey('User', on_delete=models.CASCADE, related_name='learner_links')
    learner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='parent_links')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='parent_learner_links')
    relationship = models.CharField(max_length=50, default='Parent')  # Mother, Father, Guardian, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['parent', 'learner']
        unique_together = ['parent', 'learner']

    def __str__(self):
        return f'{self.parent.email} -> {self.learner.email}'


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='student_profiles')
    
    # CBC specific
    nemis_number = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="National Education Management Information System Number")
    assessment_number = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="KNEC Assessment Number")
    
    # MERN-like fields
    admission_number = models.CharField(max_length=50, blank=True, null=True)
    roll_number = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    
    # Contact Info
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    
    # Medical/Transport
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Additional Info
    admission_date = models.DateField(null=True, blank=True)
    previous_school = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Student Profile: {self.user.email}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE, related_name='teacher_profiles')
    
    # MERN-like fields
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    marital_status = models.CharField(max_length=20, choices=[('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')], blank=True)
    
    # Kenyan specifics
    national_id = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="Kenyan National ID")
    kra_pin = models.CharField(max_length=50, blank=True, null=True, unique=True, help_text="KRA PIN Number")
    
    # Contact Info
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Professional Info
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=50, choices=[('Full-Time', 'Full-Time'), ('Part-Time', 'Part-Time'), ('Contract', 'Contract'), ('Intern', 'Intern')], default='Full-Time')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Teacher Profile: {self.user.email}"
