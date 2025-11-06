from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from admin_panel.models import AdminUser, FraudRule, FraudAlert
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from admin_panel.constants import SENIOR_ADMIN, OPERATIONAL_ADMIN, FRAUD_SUSPICIOUS_WITHDRAWAL
from unittest.mock import patch

User = get_user_model()


class AuthenticationTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
    
    def test_login_success(self):
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['role'], SENIOR_ADMIN)
    
    def test_login_non_admin_user(self):
        regular_user = User.objects.create_user(
            email='regular@test.com',
            password='testpass123'
        )
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'regular@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserManagementViewSetTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=self.admin_user_obj,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.test_user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_list_users(self):
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_users_by_name(self):
        response = self.client.get('/api/admin/users/?name=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_search_users_by_email(self):
        response = self.client.get('/api/admin/users/?email=test@test.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_suspend_user(self):
        response = self.client.post(f'/api/admin/users/{self.test_user.id}/suspend/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.test_user.refresh_from_db()
        self.assertFalse(self.test_user.is_active)
    
    def test_reactivate_user(self):
        self.test_user.is_active = False
        self.test_user.save()
        
        response = self.client.post(f'/api/admin/users/{self.test_user.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.is_active)


class TransactionViewSetTest(TestCase):
    
    def setUp(self):
        self.patcher = patch('admin_panel.signals.detect_fraud_for_transaction.delay')
        self.mock_delay = self.patcher.start()
        
        self.client = APIClient()
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        
        self.transaction = Transaction.objects.create(
            account=self.account,
            amount=500,
            balance_after_transaction=1500,
            transaction_type=1
        )
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_list_transactions(self):
        response = self.client.get('/api/admin/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_transactions_by_type(self):
        response = self.client.get('/api/admin/transactions/?type=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_transactions_by_amount(self):
        response = self.client.get('/api/admin/transactions/?min_amount=400&max_amount=600')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FraudRuleViewSetTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_create_fraud_rule(self):
        data = {
            'name': 'Test Rule',
            'rule_type': FRAUD_SUSPICIOUS_WITHDRAWAL,
            'parameters': {'threshold': 1000},
            'is_active': True,
            'severity': 'HIGH'
        }
        response = self.client.post('/api/admin/fraud-rules/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_fraud_rules(self):
        response = self.client.get('/api/admin/fraud-rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AnalyticsViewSetTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_transaction_volume(self):
        response = self.client.get('/api/admin/analytics/transaction_volume/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_daily_trends(self):
        response = self.client.get('/api/admin/analytics/daily_trends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_statistics(self):
        response = self.client.get('/api/admin/analytics/user_statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SystemHealthViewSetTest(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        
        response = self.client.post('/api/admin/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_current_health(self):
        response = self.client.get('/api/admin/health/current/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cpu', response.data)
        self.assertIn('memory', response.data)
        self.assertIn('database', response.data)
