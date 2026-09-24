from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf_headers(self):
        response = self.client.get('/api/auth/csrf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {'HTTP_X_CSRFTOKEN': response.data['csrfToken']}




    def test_registration_creates_a_user_with_a_hashed_password(self):
        """Registration creates an account without storing its plaintext password"""
        response = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'AbcDefg!123+'},
            format='json',
            **self.csrf_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='alice')
        self.assertTrue(user.check_password('AbcDefg!123+'))




    def test_registration_rejects_weak_passwords(self):
        """Registration applies Django's password strength rules"""
        response = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'password'},
            format='json',
            **self.csrf_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='alice').exists())




    def test_registration_rejects_duplicate_username_case_insensitively(self):
        """Usernames cannot be reused with different capitalization"""
        User.objects.create_user(
            username='Alice',
            password='AbcDefg!123+',
        )

        response = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'HijKlmno!123+'},
            format='json',
            **self.csrf_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)




    def test_registration_requires_csrf_protection(self):
        """A browser must provide a CSRF token before creating an account."""
        response = self.client.post(
            '/api/auth/register/',
            {'username': 'alice', 'password': 'AbcDefg!123+'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(username='alice').exists())




    def test_login_requires_csrf_protection(self):
        """A browser must provide a CSRF token before signing in"""
        User.objects.create_user(
            'alice',
            password='AbcDefg!123+',
        )

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'alice', 'password': 'AbcDefg!123+'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)




    def test_login_rejects_invalid_credentials(self):
        """An incorrect password does not create an authenticated session"""
        User.objects.create_user(
            'alice',
            password='AbcDefg!123+',
        )

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'alice', 'password': 'AWrongPassword!123+'},
            format='json',
            **self.csrf_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'Invalid username or password.',
        )





    def test_unauthenticated_user_cannot_access_current_user(self):
        """The current-user endpoint is private only until a user signs in"""
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)




    def test_authenticated_user_can_be_read_and_logged_out(self):
        """A signed-in user can read their account and end their session"""
        User.objects.create_user(
            'alice',
            password='AbcDefg!123+',
        )
        headers = self.csrf_headers()

        login_response = self.client.post(
            '/api/auth/login/',
            {'username': 'alice', 'password': 'AbcDefg!123+'},
            format='json',
            **headers,
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        me_response = self.client.get('/api/auth/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['user']['username'], 'alice')

        logout_response = self.client.post(
            '/api/auth/logout/',
            format='json',
            HTTP_X_CSRFTOKEN=login_response.data['csrfToken'],
        )
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.client.get('/api/auth/me/').status_code,
            status.HTTP_403_FORBIDDEN,
        )




    def test_logout_requires_csrf_protection(self):
        """A missing CSRF token cannot sign a user out or end their session"""
        User.objects.create_user(
            'alice',
            password='AbcDefg!123+',
        )
        headers = self.csrf_headers()

        login_response = self.client.post(
            '/api/auth/login/',
            {'username': 'alice', 'password': 'AbcDefg!123+'},
            format='json',
            **headers,
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            '/api/auth/logout/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Failed logout attempt importantly must not destroy the authenticated session
        self.assertEqual(
            self.client.get('/api/auth/me/').status_code,
            status.HTTP_200_OK,
        )
