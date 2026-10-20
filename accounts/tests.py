from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from tenants.models import School


User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class AuthenticationTests(TestCase):
    """Test authentication flows: login, refresh, password reset."""

    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(
            name='Test School',
            code='test-school',
            address='123 Test St',
            phone='+254700000000',
            email='admin@testschool.com',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@testschool.com',
            password='AdminPass123',
            role='ADMIN',
            school=self.school,
            is_staff=True,
        )
        self.teacher_user = User.objects.create_user(
            email='teacher@testschool.com',
            password='TeacherPass123',
            role='TEACHER',
            school=self.school,
        )
        self.student_user = User.objects.create_user(
            email='student@testschool.com',
            password='StudentPass123',
            role='STUDENT',
            school=self.school,
        )
        self.parent_user = User.objects.create_user(
            email='parent@testschool.com',
            password='ParentPass123',
            role='PARENT',
            school=self.school,
        )
        self.staff_user = User.objects.create_user(
            email='staff@testschool.com',
            password='StaffPass123',
            role='STAFF',
            school=self.school,
        )

    def test_admin_can_login_with_valid_credentials(self):
        """POST /api/auth/login/ with valid admin credentials returns tokens."""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@testschool.com',
            'password': 'AdminPass123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'ADMIN')

    def test_login_with_invalid_password_returns_401(self):
        """POST /api/auth/login/ with wrong password returns 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@testschool.com',
            'password': 'WrongPassword',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_with_nonexistent_email_returns_401(self):
        """POST /api/auth/login/ with unknown email returns 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@testschool.com',
            'password': 'AnyPassword',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_with_missing_fields_returns_400(self):
        """POST /api/auth/login/ with missing fields returns 400."""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@testschool.com',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_teacher_can_login(self):
        """Teacher can authenticate with valid credentials."""
        response = self.client.post('/api/auth/login/', {
            'email': 'teacher@testschool.com',
            'password': 'TeacherPass123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'TEACHER')

    def test_student_can_login(self):
        """Student can authenticate with valid credentials."""
        response = self.client.post('/api/auth/login/', {
            'email': 'student@testschool.com',
            'password': 'StudentPass123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'STUDENT')

    def test_parent_can_login(self):
        """Parent can authenticate with valid credentials."""
        response = self.client.post('/api/auth/login/', {
            'email': 'parent@testschool.com',
            'password': 'ParentPass123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'PARENT')

    def test_staff_can_login(self):
        """Staff can authenticate with valid credentials."""
        response = self.client.post('/api/auth/login/', {
            'email': 'staff@testschool.com',
            'password': 'StaffPass123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'STAFF')

    def test_jwt_refresh_with_valid_token(self):
        """POST /api/auth/refresh/ with valid refresh token returns new access token."""
        tokens = get_tokens_for_user(self.admin_user)
        response = self.client.post('/api/auth/refresh/', {
            'refresh': tokens['refresh'],
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_jwt_refresh_with_invalid_token_returns_401(self):
        """POST /api/auth/refresh/ with invalid token returns 401."""
        response = self.client.post('/api/auth/refresh/', {
            'refresh': 'invalid.token.here',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_access_returns_401(self):
        """Accessing protected endpoint without token returns 401."""
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 401)


class RoleBasedAccessTests(TestCase):
    """Test that each role can only access authorized features."""

    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(
            name='Test School',
            code='test-school',
            address='123 Test St',
            phone='+254700000000',
            email='admin@testschool.com',
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email='admin@testschool.com',
            password='AdminPass123',
            role='ADMIN',
            school=self.school,
            is_staff=True,
        )
        self.teacher_user = User.objects.create_user(
            email='teacher@testschool.com',
            password='TeacherPass123',
            role='TEACHER',
            school=self.school,
        )
        self.student_user = User.objects.create_user(
            email='student@testschool.com',
            password='StudentPass123',
            role='STUDENT',
            school=self.school,
        )
        self.admin_tokens = get_tokens_for_user(self.admin_user)
        self.teacher_tokens = get_tokens_for_user(self.teacher_user)
        self.student_tokens = get_tokens_for_user(self.student_user)

    def test_admin_can_access_website_config(self):
        """ADMIN can GET website config."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_access_website_config(self):
        """TEACHER cannot access website config (403)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_website_config(self):
        """STUDENT cannot access website config (403)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_tokens["access"]}')
        response = self.client.get('/api/website/config/')
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_access_academics(self):
        """TEACHER can access academics endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_tokens["access"]}')
        response = self.client.get('/api/academics/grades/')
        self.assertIn(response.status_code, [200, 404])

    def test_student_can_access_academics(self):
        """STUDENT can access academics endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_tokens["access"]}')
        response = self.client.get('/api/academics/grades/')
        self.assertIn(response.status_code, [200, 404])


class PasswordResetSecurityTests(TestCase):
    """Test that password reset does not reveal whether an email exists."""

    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(
            name='Test School', code='pr-school', address='A', phone='1', email='pr@s.com',
        )
        self.existing_user = User.objects.create_user(
            email='existing@testschool.com', password='SomePass123', role='STUDENT', school=self.school,
        )

    def test_password_reset_returns_same_response_for_unknown_email(self):
        """Requesting reset for non-existent email returns same 200 status."""
        resp_unknown = self.client.post('/api/auth/password-reset/request/', {'email': 'nobody@nowhere.com'}, format='json')
        self.assertEqual(resp_unknown.status_code, 200)

    def test_password_reset_does_not_reveal_email_existence(self):
        """Both existing and non-existing emails return 200 with same base message."""
        resp_existing = self.client.post('/api/auth/password-reset/request/', {'email': 'existing@testschool.com'}, format='json')
        resp_unknown = self.client.post('/api/auth/password-reset/request/', {'email': 'nobody@nowhere.com'}, format='json')

        # Both must return 200 OK
        self.assertEqual(resp_existing.status_code, resp_unknown.status_code)

        # Both must contain the same generic message
        existing_msg = resp_existing.json().get('detail', '')
        unknown_msg = resp_unknown.json().get('detail', '')
        self.assertEqual(existing_msg, unknown_msg)
        self.assertIn('If an account exists', unknown_msg)
