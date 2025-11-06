from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from admin_panel.models import FraudRule, FraudAlert, AdminUser
from admin_panel.fraud_detector import FraudDetector
from admin_panel.constants import (
    FRAUD_SUSPICIOUS_WITHDRAWAL,
    FRAUD_UNUSUAL_HOURS,
    FRAUD_REPEATED_TRANSACTIONS,
    FRAUD_EXCEEDS_MAX_AMOUNT,
    SENIOR_ADMIN
)
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL, DEPOSIT
from unittest.mock import patch

User = get_user_model()


class FraudDetectionTest(TestCase):
    
    def setUp(self):
        self.patcher = patch('admin_panel.signals.detect_fraud_for_transaction.delay')
        self.mock_delay = self.patcher.start()
        
        admin_user_obj = User.objects.create_user(
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user = AdminUser.objects.create(
            user=admin_user_obj,
            role=SENIOR_ADMIN
        )
        
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
            balance=10000
        )
        
        self.detector = FraudDetector()
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_suspicious_withdrawal_detection(self):
        rule = FraudRule.objects.create(
            name='Large Withdrawal',
            rule_type=FRAUD_SUSPICIOUS_WITHDRAWAL,
            parameters={'amount_threshold': 5000, 'percentage_of_balance': 80},
            is_active=True,
            created_by=self.admin_user
        )
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=6000,
            balance_after_transaction=4000,
            transaction_type=WITHDRAWAL
        )
        
        alerts = self.detector.check_transaction(transaction)
        self.assertGreater(len(alerts), 0)
    
    def test_unusual_hours_detection(self):
        rule = FraudRule.objects.create(
            name='After Hours',
            rule_type=FRAUD_UNUSUAL_HOURS,
            parameters={'start_hour': 22, 'end_hour': 6},
            is_active=True,
            created_by=self.admin_user
        )
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=500,
            balance_after_transaction=10500,
            transaction_type=DEPOSIT
        )
        transaction.timestamp = transaction.timestamp.replace(hour=23)
        transaction.save()
        
        alerts = self.detector.check_transaction(transaction)
        self.assertGreater(len(alerts), 0)
    
    def test_exceeds_max_amount_detection(self):
        rule = FraudRule.objects.create(
            name='Exceeds Max After Hours',
            rule_type=FRAUD_EXCEEDS_MAX_AMOUNT,
            parameters={
                'max_amount': 5000,
                'time_restriction_start': 22,
                'time_restriction_end': 6
            },
            is_active=True,
            created_by=self.admin_user
        )
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=6000,
            balance_after_transaction=16000,
            transaction_type=DEPOSIT
        )
        transaction.timestamp = transaction.timestamp.replace(hour=23)
        transaction.save()
        
        alerts = self.detector.check_transaction(transaction)
        self.assertGreater(len(alerts), 0)
    
    def test_no_alert_for_normal_transaction(self):
        rule = FraudRule.objects.create(
            name='Large Withdrawal',
            rule_type=FRAUD_SUSPICIOUS_WITHDRAWAL,
            parameters={'amount_threshold': 5000, 'percentage_of_balance': 80},
            is_active=True,
            created_by=self.admin_user
        )
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100,
            balance_after_transaction=10100,
            transaction_type=DEPOSIT
        )
        
        alerts = self.detector.check_transaction(transaction)
        self.assertEqual(len(alerts), 0)
