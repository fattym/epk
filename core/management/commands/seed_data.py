from django.core.management.base import BaseCommand
from tenants.models import School, SchoolSettings
from accounts.models import User
from academics.models import (
    Grade, Pathway, Stream, LearningArea,
    Strand, SubStrand, LearningOutcome, RubricDescriptor, Term,
)


class Command(BaseCommand):
    help = 'Seed initial data for development including CBC curriculum'

    def handle(self, *args, **options):
        school, created = School.objects.get_or_create(
            code='demo-school',
            defaults={
                'name': 'Demo School',
                'address': '123 Main St',
                'phone': '+254700000000',
                'email': 'admin@demoschool.com',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created school: {school.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'School already exists: {school.name}'))

        settings, created = SchoolSettings.objects.get_or_create(
            school=school,
            defaults={
                'academic_year': '2025/2026',
                'current_term': 'Term 1',
                'currency': 'KES',
                'timezone': 'Africa/Nairobi',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created school settings'))

        admin, created = User.objects.get_or_create(
            email='admin@demoschool.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'ADMIN',
                'school': school,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin@demoschool.com / admin123'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))

        levels = [
            ('Pre-Primery 1', 'pre_primary', 1),
            ('Pre-Primery 2', 'pre_primary', 2),
            ('Grade 1', 'primary', 3),
            ('Grade 2', 'primary', 4),
            ('Grade 3', 'primary', 5),
            ('Grade 4', 'primary', 6),
            ('Grade 5', 'primary', 7),
            ('Grade 6', 'primary', 8),
            ('Grade 7', 'junior_secondary', 9),
            ('Grade 8', 'junior_secondary', 10),
            ('Grade 9', 'junior_secondary', 11),
            ('Grade 10', 'senior_secondary', 12),
            ('Grade 11', 'senior_secondary', 13),
            ('Grade 12', 'senior_secondary', 14),
        ]
        for name, stage, order in levels:
            Grade.objects.get_or_create(name=name, stage=stage, order=order)
        self.stdout.write(self.style.SUCCESS('Created grades'))

        grade4 = Grade.objects.get(name='Grade 4')
        Stream.objects.get_or_create(name='East', grade=grade4, school=school)
        Stream.objects.get_or_create(name='West', grade=grade4, school=school)
        self.stdout.write(self.style.SUCCESS('Created streams for Grade 4'))

        pathways = [
            'STEM',
            'Social Sciences',
            'Arts & Sports',
            'Vocational Track',
        ]
        for name in pathways:
            Pathway.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS('Created pathways'))

        math = LearningArea.objects.get_or_create(
            name='Mathematics', code='MATH', grade=grade4, school=school
        )[0]
        eng = LearningArea.objects.get_or_create(
            name='English', code='ENG', grade=grade4, school=school
        )[0]

        math_strand = Strand.objects.get_or_create(learning_area=math, name='Numbers')[0]
        SubStrand.objects.get_or_create(strand=math_strand, name='Addition and Subtraction')
        self.stdout.write(self.style.SUCCESS('Created sample learning areas and strands'))

        term = Term.objects.get_or_create(
            name='Term 1', academic_year='2025/2026', school=school,
            defaults={'start_date': '2025-01-06', 'end_date': '2025-04-04', 'is_current': True}
        )[0]
        self.stdout.write(self.style.SUCCESS('Created sample term'))
