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
    )
    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    school = models.ForeignKey('tenants.School', on_delete=models.CASCADE)
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
