from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from .models import FraudRule, FraudAlert, AdminAuditLog

User = get_user_model()


class AdminAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='SUPER_ADMIN'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role='REGULAR_USER'
        )
    
    def test_admin_login_success(self):
        response = self.client.post(reverse('admin_panel:login'), {
            'username': 'admin@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AdminAuditLog.objects.filter(user=self.admin_user, action='Admin Login').exists())
    
    def test_regular_user_cannot_login_to_admin(self):
        response = self.client.post(reverse('admin_panel:login'), {
            'username': 'user@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AdminAuditLog.objects.filter(user=self.regular_user, action='Admin Login').exists())
    
    def test_admin_logout(self):
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin_panel:logout'))
        self.assertEqual(response.status_code, 302)


class AdminMiddlewareTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='MANAGER'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role='REGULAR_USER'
        )
    
    def test_middleware_blocks_regular_users(self):
        self.client.login(username='user@test.com', password='testpass123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_middleware_allows_admin_users(self):
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)


class FraudRuleTests(TestCase):
    def test_fraud_rule_creation(self):
        rule = FraudRule.objects.create(
            name='High Value Transaction',
            description='Detects transactions over $10000',
            rule_type='HIGH_VALUE',
            threshold_value=10000,
            is_active=True
        )
        self.assertEqual(str(rule), 'High Value Transaction')
        self.assertTrue(rule.is_active)


class FraudAlertTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        self.rule = FraudRule.objects.create(
            name='Test Rule',
            description='Test',
            rule_type='HIGH_VALUE',
            is_active=True
        )
    
    def test_fraud_alert_creation(self):
        alert = FraudAlert.objects.create(
            account=self.account,
            rule=self.rule,
            severity='HIGH',
            description='Test alert',
            status='PENDING'
        )
        self.assertEqual(alert.status, 'PENDING')
        self.assertEqual(alert.severity, 'HIGH')


class AdminAuditLogTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='SUPER_ADMIN'
        )
    
    def test_audit_log_creation(self):
        log = AdminAuditLog.objects.create(
            user=self.admin_user,
            action='Test Action',
            target_model='User',
            target_id=1,
            ip_address='127.0.0.1'
        )
        self.assertIn('admin@test.com', str(log))
        self.assertEqual(log.action, 'Test Action')


class UsersDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role='MANAGER'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.test_user = User.objects.create_user(
            email='testuser@test.com',
            password='testpass123'
        )
        UserBankAccount.objects.create(
            user=self.test_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender='M',
            balance=500
        )
    
    def test_users_dashboard_accessible(self):
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin_panel:users_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser@test.com')
    
    def test_user_search(self):
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin_panel:users_dashboard') + '?search=testuser')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser@test.com')
