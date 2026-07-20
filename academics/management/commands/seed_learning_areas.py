from django.core.management.base import BaseCommand
from django.db import transaction
from academics.models import LearningArea, Grade
from tenants.models import School

# CBC Learning Areas grouped by stage.
# Each tuple: (code, name) -> mapped below to the first grade of its stage.
GROUPS = {
    'pre_primary': [
        ('LA', 'Language Activities'),
        ('MA', 'Mathematical Activities'),
        ('EA', 'Environmental Activities'),
        ('PCA', 'Psychomotor and Creative Activities'),
        ('REA', 'Religious Education Activities'),
    ],
    'primary': [
        ('ENG', 'English'),
        ('KIS', 'Kiswahili'),
        ('KSL', 'Kenyan Sign Language'),
        ('MA', 'Mathematical Activities'),
        ('EA', 'Environmental Activities'),
        ('HNA', 'Hygiene and Nutrition Activities'),
        ('RE', 'Religious Education (CRE/IRE/HRE)'),
        ('MCA', 'Movement and Creative Activities'),
        ('MATH', 'Mathematics'),
        ('SCI', 'Science and Technology'),
        ('AGR', 'Agriculture'),
        ('HS', 'Home Science'),
        ('CA', 'Creative Arts'),
        ('PHE', 'Physical and Health Education'),
        ('SS', 'Social Studies'),
    ],
    'junior_secondary': [
        ('ENG', 'English'),
        ('KIS', 'Kiswahili'),
        ('KSL', 'Kenyan Sign Language'),
        ('MATH', 'Mathematics'),
        ('SCI', 'Integrated Science'),
        ('HE', 'Health Education'),
        ('PTPC', 'Pre-Technical and Pre-Career Education'),
        ('SS', 'Social Studies'),
        ('RE', 'Religious Education'),
        ('AGR', 'Agriculture'),
        ('BS', 'Business Studies'),
        ('LSE', 'Life Skills Education'),
        ('SPE', 'Sports and Physical Education'),
        ('VA', 'Visual Arts'),
        ('PA', 'Performing Arts'),
        ('HS', 'Home Science'),
        ('CS', 'Computer Science'),
    ],
}

# Representative grade per stage (first grade of the stage).
STAGE_GRADE_ORDER = {
    'pre_primary': 1,      # Pre-Primary 1
    'primary': 3,          # Grade 1
    'junior_secondary': 9, # Grade 7
}


class Command(BaseCommand):
    help = 'Seed CBC Learning Areas grouped by stage (Pre-Primary, Lower/Upper Primary, Junior Secondary).'

    def add_arguments(self, parser):
        parser.add_argument('--school', type=int, default=None,
                            help='School id to attach areas to. Defaults to the first school.')
        parser.add_argument('--replace', action='store_true',
                            help='Delete existing learning areas for the target school before seeding.')

    @transaction.atomic
    def handle(self, *args, **options):
        school = None
        if options['school']:
            school = School.objects.filter(id=options['school']).first()
        if not school:
            school = School.objects.first()
        if not school:
            self.stderr.write('No school found. Create a school first.')
            return

        if options['replace']:
            deleted, _ = LearningArea.objects.filter(school=school).delete()
            self.stdout.write(f'Deleted {deleted} existing learning areas for school {school.id}.')

        grade_by_stage = {}
        for stage, order in STAGE_GRADE_ORDER.items():
            grade = Grade.objects.filter(stage=stage, order=order).first()
            grade_by_stage[stage] = grade

        created = 0
        skipped = 0
        labels = {
            'pre_primary': 'Pre-Primary (PP1 & PP2)',
            'primary': 'Primary (Grade 1–6)',
            'junior_secondary': 'Junior Secondary (Grade 7–9)',
        }
        for stage, areas in GROUPS.items():
            grade = grade_by_stage[stage]
            if not grade:
                self.stderr.write(f'No grade found for stage {stage}; skipping.')
                continue
            self.stdout.write(f'\n=== {labels[stage]} -> {grade.name} ===')
            for code, name in areas:
                obj, was_created = LearningArea.objects.get_or_create(
                    school=school, grade=grade, code=code,
                    defaults={'name': name},
                )
                if was_created:
                    created += 1
                    self.stdout.write(f'  + [{code}] {name}')
                else:
                    skipped += 1
                    self.stdout.write(f'  = [{code}] {name} (exists)')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. Created {created}, skipped {skipped} for school "{school.name}" (id={school.id}).'
            )
        )
