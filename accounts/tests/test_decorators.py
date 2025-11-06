from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from accounts.decorators import admin_required, permission_required
from accounts.models import VIEW_USERS, EDIT_USERS

User = get_user_model()


class AdminRequiredDecoratorTest(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_staff=False
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_admin_required_blocks_non_staff(self):
        @admin_required
        def test_view(request):
            return HttpResponse('OK')
        
        request = self.factory.get('/admin-portal/users/')
        request.user = self.user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin-portal/login/', response.url)
    
    def test_admin_required_allows_staff(self):
        @admin_required
        def test_view(request):
            return HttpResponse('OK')
        
        request = self.factory.get('/admin-portal/users/')
        request.user = self.admin
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')
    
    def test_admin_required_blocks_unauthenticated(self):
        from django.contrib.auth.models import AnonymousUser
        
        @admin_required
        def test_view(request):
            return HttpResponse('OK')
        
        request = self.factory.get('/admin-portal/users/')
        request.user = AnonymousUser()
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)


class PermissionRequiredDecoratorTest(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_with_permission = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[VIEW_USERS, EDIT_USERS]
        )
        self.admin_without_permission = User.objects.create_user(
            email='admin2@example.com',
            password='testpass123',
            is_staff=True,
            admin_permissions=[]
        )
    
    def test_permission_required_allows_with_permission(self):
        @permission_required(VIEW_USERS)
        def test_view(request):
            return HttpResponse('OK')
        
        request = self.factory.get('/admin-portal/users/')
        request.user = self.admin_with_permission
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
    
    def test_permission_required_blocks_without_permission(self):
        @permission_required(VIEW_USERS)
        def test_view(request):
            return HttpResponse('OK')
        
        request = self.factory.get('/admin-portal/users/')
        request.user = self.admin_without_permission
        
        with self.assertRaises(PermissionDenied):
            test_view(request)
