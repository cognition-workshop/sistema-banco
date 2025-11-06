from django.test import TestCase
from django.contrib.auth import get_user_model
from admin_panel.analytics import Analytics
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from unittest.mock import patch

User = get_user_model()


class AnalyticsTest(TestCase):
    
    def setUp(self):
        self.patcher = patch('admin_panel.signals.detect_fraud_for_transaction.delay')
        self.mock_delay = self.patcher.start()
        
        self.analytics = Analytics()
        
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
        
        Transaction.objects.create(
            account=self.account,
            amount=500,
            balance_after_transaction=1500,
            transaction_type=1
        )
        Transaction.objects.create(
            account=self.account,
            amount=200,
            balance_after_transaction=1300,
            transaction_type=2
        )
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_transaction_volume_by_type(self):
        result = self.analytics.get_transaction_volume_by_type()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_daily_trends(self):
        result = self.analytics.get_daily_trends(days=7)
        self.assertIsInstance(result, list)
    
    def test_user_statistics(self):
        result = self.analytics.get_user_statistics()
        self.assertIsInstance(result, dict)
        self.assertIn('total_users', result)
        self.assertIn('active_users', result)
        self.assertIn('total_balance', result)
