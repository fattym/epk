from django.core.management.base import BaseCommand
from accounts.models import User
from distributor.models import DistributorProfile, DistributorWallet


class Command(BaseCommand):
    help = "Create a main super admin and a distributor account."

    def add_arguments(self, parser):
        parser.add_argument('--admin-email', default='admin@codingclubs.co.ke')
        parser.add_argument('--admin-password', default='Admin@123')
        parser.add_argument('--distributor-email', default='distributor@codingclubs.co.ke')
        parser.add_argument('--distributor-password', default='Distributor@123')
        parser.add_argument('--company-name', default='Demo Distributor Ltd')
        parser.add_argument('--phone', default='0798734442')

    def handle(self, *args, **options):
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        dist_email = options['distributor_email']
        dist_password = options['distributor_password']
        company = options['company_name']
        phone = options['phone']

        if User.objects.filter(email=admin_email).exists():
            admin = User.objects.get(email=admin_email)
            self.stdout.write(self.style.WARNING(f'Admin already exists: {admin.email}'))
        else:
            admin = User.objects.create_superuser(email=admin_email, password=admin_password)
            admin.first_name = 'Super'
            admin.last_name = 'Admin'
            admin.role = 'ADMIN'
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created super admin: {admin.email}'))

        if User.objects.filter(email=dist_email).exists():
            dist_user = User.objects.get(email=dist_email)
            self.stdout.write(self.style.WARNING(f'Distributor user already exists: {dist_user.email}'))
        else:
            dist_user = User.objects.create_user(
                email=dist_email, password=dist_password, role='DISTRIBUTOR',
                first_name='John', last_name='Distributor', phone=phone,
            )
            self.stdout.write(self.style.SUCCESS(f'Created distributor user: {dist_user.email}'))

        profile, created = DistributorProfile.objects.get_or_create(
            user=dist_user,
            defaults={
                'company_name': company,
                'registration_number': 'REG-001',
                'address': 'Nairobi, Kenya',
                'phone': phone,
                'email': dist_email,
                'is_verified': True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created distributor profile: {profile.company_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Distributor profile already exists: {profile.company_name}'))

        DistributorWallet.objects.get_or_create(distributor=profile)

        self.stdout.write(self.style.SUCCESS(f'\nDone. Admin: {admin_email} | Distributor: {dist_email}'))
        self.stdout.write(self.style.SUCCESS(f'API: POST /api/distributor/profiles/ to list/approve/suspend distributors.'))