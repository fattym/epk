from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tenants.models import School
from website.models import WebsiteConfig


User = get_user_model()


def get_tokens_for_user(user):
    """Return access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class WebsiteConfigTestCase(TestCase):
    """Base test case for Website Builder tests."""

    def setUp(self):
        self.client = APIClient()

        # Create two schools for tenant isolation tests
        self.school1 = School.objects.create(
            name='Demo School',
            code='demo-school',
            address='123 Main St, Nairobi',
            phone='+254700000000',
            email='admin@demoschool.com',
            is_active=True,
        )
        self.school2 = School.objects.create(
            name='Second School',
            code='second-school',
            address='456 Second St, Mombasa',
            phone='+254700000001',
            email='admin@secondschool.com',
            is_active=True,
        )

        # Create admin users for each school
        self.admin1 = User.objects.create_user(
            email='admin1@demoschool.com',
            password='AdminPass123',
            role='ADMIN',
            school=self.school1,
            is_staff=True,
        )
        self.admin2 = User.objects.create_user(
            email='admin2@secondschool.com',
            password='AdminPass123',
            role='ADMIN',
            school=self.school2,
            is_staff=True,
        )

        # Create a teacher user (should NOT be able to manage website)
        self.teacher1 = User.objects.create_user(
            email='teacher1@demoschool.com',
            password='TeacherPass123',
            role='TEACHER',
            school=self.school1,
        )

        # Create a student user (should NOT be able to manage website)
        self.student1 = User.objects.create_user(
            email='student1@demoschool.com',
            password='StudentPass123',
            role='STUDENT',
            school=self.school1,
        )

        # Get auth tokens
        self.admin1_tokens = get_tokens_for_user(self.admin1)
        self.admin2_tokens = get_tokens_for_user(self.admin2)
        self.teacher1_tokens = get_tokens_for_user(self.teacher1)
        self.student1_tokens = get_tokens_for_user(self.student1)


class WebsiteConfigCRUDTests(WebsiteConfigTestCase):
    """Test website configuration CRUD operations."""

    def test_get_config_creates_default(self):
        """GET /api/website/config/ should create a default config if none exists."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['school'], self.school1.id)
        self.assertEqual(data['status'], 'draft')
        self.assertIn('hero', data['sections'])
        self.assertIn('about', data['sections'])
        self.assertTrue(WebsiteConfig.objects.filter(school=self.school1).exists())

    def test_get_config_returns_existing(self):
        """GET should return existing config without creating a duplicate."""
        WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
            display_name='My School',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['status'], 'published')
        self.assertEqual(data['display_name'], 'My School')
        # Should not create duplicate
        self.assertEqual(WebsiteConfig.objects.filter(school=self.school1).count(), 1)

    def test_update_config(self):
        """PUT /api/website/config/update/ should update website config."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='draft',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.put('/api/website/config/update/', {
            'display_name': 'Updated School Name',
            'tagline': 'Excellence in Education',
            'primary_color': '#16a085',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.display_name, 'Updated School Name')
        self.assertEqual(config.tagline, 'Excellence in Education')
        self.assertEqual(config.primary_color, '#16a085')
        self.assertIsNotNone(config.last_saved_at)

    def test_update_config_partial(self):
        """PATCH /api/website/config/update/ should do partial update."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='draft',
            display_name='Original Name',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.patch('/api/website/config/update/', {
            'tagline': 'New tagline',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.display_name, 'Original Name')  # unchanged
        self.assertEqual(config.tagline, 'New tagline')

    def test_cannot_delete_config(self):
        """DELETE should return 405 - website config cannot be deleted."""
        WebsiteConfig.objects.create(school=self.school1, status='draft')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.delete('/api/website/config/')
        self.assertEqual(response.status_code, 405)


class WebsitePublishTests(WebsiteConfigTestCase):
    """Test publish/unpublish workflow."""

    def test_publish_website(self):
        """POST /api/website/config/publish/ should set status to published."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='draft',
            homepage_title='Welcome',
            display_name='Demo School',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.post('/api/website/config/publish/')
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.status, 'published')
        self.assertIsNotNone(config.published_at)

    def test_unpublish_website(self):
        """POST /api/website/config/unpublish/ should set status to unpublished."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.post('/api/website/config/unpublish/')
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.status, 'unpublished')
        self.assertIsNone(config.published_at)

    def test_reset_defaults(self):
        """POST /api/website/config/reset_defaults/ should restore defaults."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
            display_name='Custom Name',
            tagline='Custom tagline',
            primary_color='#ff0000',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.post('/api/website/config/reset_defaults/')
        self.assertEqual(response.status_code, 200)
        config.refresh_from_db()
        self.assertEqual(config.status, 'draft')
        self.assertEqual(config.display_name, '')
        self.assertEqual(config.tagline, '')
        self.assertEqual(config.primary_color, '#2563eb')


class WebsitePermissionTests(WebsiteConfigTestCase):
    """Test role-based permissions for website management."""

    def test_teacher_cannot_manage_website(self):
        """TEACHER role should get 403 on website endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher1_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_manage_website(self):
        """STUDENT role should get 403 on website endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student1_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_manage_website(self):
        """Unauthenticated requests should get 401."""
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 401)

    def test_cannot_access_other_school_config(self):
        """School 1 admin cannot access school 2's website config."""
        WebsiteConfig.objects.create(school=self.school2, status='published')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin1_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['school'], self.school1.id)  # Should return school1's config


class PublicWebsiteTests(WebsiteConfigTestCase):
    """Test public website endpoint."""

    def test_public_website_published(self):
        """GET /api/website/public/<slug>/ should return published website."""
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
            display_name='Demo School Public',
            homepage_title='Welcome to Demo School',
            about_school='About our school.',
        )
        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['school']['name'], 'Demo School')
        self.assertEqual(data['branding']['display_name'], 'Demo School Public')
        self.assertEqual(data['branding']['homepage_title'], 'Welcome to Demo School')
        self.assertEqual(data['content']['about_school'], 'About our school.')

    def test_public_website_unpublished_returns_404(self):
        """GET should return 404 for unpublished website."""
        WebsiteConfig.objects.create(
            school=self.school1,
            status='unpublished',
        )
        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 404)

    def test_public_website_draft_returns_404(self):
        """GET should return 404 for draft website."""
        WebsiteConfig.objects.create(
            school=self.school1,
            status='draft',
        )
        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 404)

    def test_public_website_invalid_slug_returns_404(self):
        """GET should return 404 for non-existent school slug."""
        response = self.client.get('/api/website/public/non-existent-school/')
        self.assertEqual(response.status_code, 404)

    def test_public_website_no_config_returns_404(self):
        """GET should return 404 when school has no website config."""
        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 404)

    def test_public_website_only_published_notices(self):
        """Public website should only show published notices."""
        from notices.models import Notice
        config = WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
        )
        Notice.objects.create(
            school=self.school1,
            title='Published Notice',
            content='This is published',
            is_published=True,
            target_type='ALL',
        )
        Notice.objects.create(
            school=self.school1,
            title='Draft Notice',
            content='This is not published',
            is_published=False,
            target_type='ALL',
        )
        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        notice_titles = [n['title'] for n in data['notices']]
        self.assertIn('Published Notice', notice_titles)
        self.assertNotIn('Draft Notice', notice_titles)

    def test_public_website_tenant_isolation(self):
        """Public website for school 1 should not show school 2's data."""
        from notices.models import Notice
        from events.models import Event
        from shop.models import Product, ProductCategory

        config1 = WebsiteConfig.objects.create(
            school=self.school1,
            status='published',
        )
        config2 = WebsiteConfig.objects.create(
            school=self.school2,
            status='published',
        )

        # Create data for school 1
        Notice.objects.create(
            school=self.school1,
            title='School 1 Notice',
            content='S1',
            is_published=True,
            target_type='ALL',
        )
        Notice.objects.create(
            school=self.school2,
            title='School 2 Notice',
            content='S2',
            is_published=True,
            target_type='ALL',
        )

        response = self.client.get(f'/api/website/public/{self.school1.code}/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        notice_titles = [n['title'] for n in data['notices']]
        self.assertIn('School 1 Notice', notice_titles)
        self.assertNotIn('School 2 Notice', notice_titles)
        self.assertEqual(data['school']['name'], 'Demo School')
        self.assertNotEqual(data['school']['name'], 'Second School')
