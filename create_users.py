import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, StudentProfile, TeacherProfile
from tenants.models import School

school, _ = School.objects.get_or_create(name='Demo School', defaults={'domain': 'demo.school.com'})

# Create Teacher
teacher, created = User.objects.get_or_create(
    email='teacher@demo.com',
    defaults={'first_name': 'Demo', 'last_name': 'Teacher', 'role': 'TEACHER', 'school': school}
)
teacher.set_password('Teacher@1234')
teacher.save()
TeacherProfile.objects.get_or_create(user=teacher, school=school, defaults={'employee_id': 'TCH-001'})

# Create Student
student, created = User.objects.get_or_create(
    email='student@demo.com',
    defaults={'first_name': 'Demo', 'last_name': 'Student', 'role': 'STUDENT', 'school': school}
)
student.set_password('1234')
student.save()
StudentProfile.objects.get_or_create(user=student, school=school, defaults={'admission_number': 'STD-001'})

print(f"Teacher created: {teacher.email} / Teacher@1234")
print(f"Student created: admission_number: STD-001 / pin: 1234")
