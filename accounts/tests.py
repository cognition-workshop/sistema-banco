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


class UserManagementViewTest(TestCase):
    
    def setUp(self):
        from accounts.models import VIEW_USERS, EDIT_USERS
        self.client = Client()
        self.admin_with_view = User.objects.create_user(
            email='admin_view@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[VIEW_USERS]
        )
        self.admin_with_edit = User.objects.create_user(
            email='admin_edit@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[VIEW_USERS, EDIT_USERS]
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_staff=False
        )
    
    def test_user_management_requires_admin(self):
        self.client.login(username='user@example.com', password='testpass123')
        response = self.client.get('/accounts/admin-portal/users/')
        self.assertEqual(response.status_code, 302)
    
    def test_user_management_requires_view_permission(self):
        admin_no_perm = User.objects.create_user(
            email='admin_no_perm@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[]
        )
        self.client.login(username='admin_no_perm@example.com', password='testpass123')
        response = self.client.get('/accounts/admin-portal/users/')
        self.assertEqual(response.status_code, 403)
    
    def test_user_management_view_loads_with_permission(self):
        self.client.login(username='admin_view@example.com', password='testpass123')
        response = self.client.get('/accounts/admin-portal/users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')
    
    def test_user_management_pagination(self):
        for i in range(30):
            User.objects.create_user(
                email=f'user{i}@example.com',
                password='testpass123'
            )
        
        self.client.login(username='admin_view@example.com', password='testpass123')
        response = self.client.get('/accounts/admin-portal/users/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['users']), 25)
    
    def test_user_management_filters(self):
        self.client.login(username='admin_view@example.com', password='testpass123')
        
        response = self.client.get('/accounts/admin-portal/users/?email=admin_view')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin_view@example.com')
    
    def test_toggle_user_active_requires_edit_permission(self):
        self.client.login(username='admin_view@example.com', password='testpass123')
        response = self.client.post(f'/accounts/admin-portal/users/{self.regular_user.id}/toggle-active/')
        self.assertEqual(response.status_code, 403)
    
    def test_toggle_user_active_works_with_permission(self):
        self.client.login(username='admin_edit@example.com', password='testpass123')
        
        initial_status = self.regular_user.is_active
        response = self.client.post(f'/accounts/admin-portal/users/{self.regular_user.id}/toggle-active/')
        
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.is_active, not initial_status)
        self.assertEqual(response.status_code, 302)
