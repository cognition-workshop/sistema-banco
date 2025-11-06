from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminLoginViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_staff=False
        )
    
    def test_admin_login_page_loads(self):
        response = self.client.get('/accounts/admin-portal/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Portal')
    
    def test_admin_user_can_login(self):
        response = self.client.post('/accounts/admin-portal/login/', {
            'username': 'admin@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get('_auth_user_id'))
    
    def test_non_staff_user_cannot_login(self):
        response = self.client.post('/accounts/admin-portal/login/', {
            'username': 'user@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You do not have admin privileges')
        self.assertFalse(self.client.session.get('_auth_user_id'))
    
    def test_invalid_credentials(self):
        response = self.client.post('/accounts/admin-portal/login/', {
            'username': 'wrong@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
