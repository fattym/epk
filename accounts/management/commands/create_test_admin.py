import secrets
import string

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from shop.models import ProductCategory
from tenants.models import School


def _gen_password(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = (
        'Create (or refresh) a test admin user for development/testing, plus a '
        'default school and category. The password is read from the '
        'TEST_ADMIN_PASSWORD env var; if unset a random one is generated and '
        'printed once. No password is ever committed to the repository.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--email', default='admin@demoschool.com')
        parser.add_argument('--school-code', default='demo-school')
        parser.add_argument('--category', default='Learning Materials')

    def handle(self, *args, **options):
        email = options['email']
        school_code = options['school_code']
        category_name = options['category']

        import os
        password = os.environ.get('TEST_ADMIN_PASSWORD') or _gen_password()

        with transaction.atomic():
            school, created = School.objects.get_or_create(
                code=school_code,
                defaults={
                    'name': 'Demo School',
                    'address': '123 Main St',
                    'phone': '+254700000000',
                    'email': 'admin@demoschool.com',
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created school: {school.name}'))

            ProductCategory.objects.get_or_create(school=school, name=category_name, parent=None)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'ADMIN',
                    'school': school,
                    'is_staff': True,
                    'is_superuser': True,
                },
            )
            if not created:
                self.stdout.write(self.style.WARNING(f'User already exists: {email}; refreshing password.'))
            user.set_password(password)
            user.role = 'ADMIN'
            user.school = school
            user.is_staff = True
            user.is_superuser = True
            user.save()

        self.stdout.write(self.style.SUCCESS('Test admin ready.'))
        self.stdout.write(f'email:    {email}')
        self.stdout.write(f'password: {password}')
        self.stdout.write(f'school:   {school.name} (code={school.code})')
        self.stdout.write('note:    run with TEST_ADMIN_PASSWORD=… to set an explicit password.')
