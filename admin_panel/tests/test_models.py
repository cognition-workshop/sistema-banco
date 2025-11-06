from django.test import TestCase
from django.contrib.auth import get_user_model
from admin_panel.models import AdminUser, AuditLog, FraudRule, FraudAlert, SystemHealthMetric
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from admin_panel.constants import SENIOR_ADMIN, FRAUD_SUSPICIOUS_WITHDRAWAL

User = get_user_model()


class AdminUserModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
    
    def test_create_admin_user(self):
        admin_user = AdminUser.objects.create(
            user=self.user,
            role=SENIOR_ADMIN,
            is_admin_active=True
        )
        self.assertEqual(admin_user.user, self.user)
        self.assertEqual(admin_user.role, SENIOR_ADMIN)
        self.assertTrue(admin_user.is_admin_active)
    
    def test_admin_user_str(self):
        admin_user = AdminUser.objects.create(
            user=self.user,
            role=SENIOR_ADMIN
        )
        expected_str = f"{self.user.email} (Senior Admin)"
        self.assertEqual(str(admin_user), expected_str)


class AuditLogModelTest(TestCase):
    
    def setUp(self):
        user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=user,
            role=SENIOR_ADMIN
        )
    
    def test_create_audit_log(self):
        audit_log = AuditLog.objects.create(
            admin_user=self.admin_user,
            action_type='CREATE',
            target_model='User',
            target_id=1,
            details={'test': 'data'},
            ip_address='127.0.0.1'
        )
        self.assertEqual(audit_log.admin_user, self.admin_user)
        self.assertEqual(audit_log.action_type, 'CREATE')
        self.assertEqual(audit_log.target_model, 'User')


class FraudRuleModelTest(TestCase):
    
    def setUp(self):
        user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=user,
            role=SENIOR_ADMIN
        )
    
    def test_create_fraud_rule(self):
        rule = FraudRule.objects.create(
            name='Test Rule',
            rule_type=FRAUD_SUSPICIOUS_WITHDRAWAL,
            parameters={'threshold': 1000},
            is_active=True,
            severity='HIGH',
            created_by=self.admin_user
        )
        self.assertEqual(rule.name, 'Test Rule')
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.created_by, self.admin_user)


class FraudAlertModelTest(TestCase):
    
    def setUp(self):
        from unittest.mock import patch
        self.patcher = patch('admin_panel.signals.detect_fraud_for_transaction.delay')
        self.mock_delay = self.patcher.start()
        
        user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN
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
        
        self.rule = FraudRule.objects.create(
            name='Test Rule',
            rule_type=FRAUD_SUSPICIOUS_WITHDRAWAL,
            parameters={'threshold': 1000},
            created_by=self.admin_user
        )
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_create_fraud_alert(self):
        alert = FraudAlert.objects.create(
            transaction=self.transaction,
            rule=self.rule,
            status='PENDING'
        )
        self.assertEqual(alert.transaction, self.transaction)
        self.assertEqual(alert.rule, self.rule)
        self.assertEqual(alert.status, 'PENDING')


class SystemHealthMetricModelTest(TestCase):
    
    def test_create_health_metric(self):
        metric = SystemHealthMetric.objects.create(
            metric_type='CPU',
            value=75.5,
            details={'usage': '75.5%'},
            status='HEALTHY'
        )
        self.assertEqual(metric.metric_type, 'CPU')
        self.assertEqual(metric.value, 75.5)
        self.assertEqual(metric.status, 'HEALTHY')
