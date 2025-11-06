from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from admin_panel.models import AdminUser
from admin_panel.permissions import IsAdminUser, IsSeniorAdmin, IsOperationalOrSeniorAdmin
from admin_panel.constants import SENIOR_ADMIN, OPERATIONAL_ADMIN, VIEWER

User = get_user_model()


class PermissionTestCase(TestCase):
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = APIView()
        
        self.senior_user = User.objects.create_user(
            email='senior@test.com',
            password='testpass123'
        )
        self.senior_admin = AdminUser.objects.create(
            user=self.senior_user,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        self.operational_user = User.objects.create_user(
            email='operational@test.com',
            password='testpass123'
        )
        self.operational_admin = AdminUser.objects.create(
            user=self.operational_user,
            role=OPERATIONAL_ADMIN,
            is_admin_active=True
        )
        
        self.viewer_user = User.objects.create_user(
            email='viewer@test.com',
            password='testpass123'
        )
        self.viewer_admin = AdminUser.objects.create(
            user=self.viewer_user,
            role=VIEWER,
            is_admin_active=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@test.com',
            password='testpass123'
        )
    
    def test_is_admin_user_permission(self):
        permission = IsAdminUser()
        
        request = self.factory.get('/')
        request.user = self.senior_user
        self.assertTrue(permission.has_permission(request, self.view))
        
        request.user = self.operational_user
        self.assertTrue(permission.has_permission(request, self.view))
        
        request.user = self.regular_user
        self.assertFalse(permission.has_permission(request, self.view))
    
    def test_is_senior_admin_permission(self):
        permission = IsSeniorAdmin()
        
        request = self.factory.get('/')
        request.user = self.senior_user
        self.assertTrue(permission.has_permission(request, self.view))
        
        request.user = self.operational_user
        self.assertFalse(permission.has_permission(request, self.view))
        
        request.user = self.viewer_user
        self.assertFalse(permission.has_permission(request, self.view))
    
    def test_is_operational_or_senior_admin_permission(self):
        permission = IsOperationalOrSeniorAdmin()
        
        request = self.factory.get('/')
        request.user = self.senior_user
        self.assertTrue(permission.has_permission(request, self.view))
        
        request.user = self.operational_user
        self.assertTrue(permission.has_permission(request, self.view))
        
        request.user = self.viewer_user
        self.assertFalse(permission.has_permission(request, self.view))
