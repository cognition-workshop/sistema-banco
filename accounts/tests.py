from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from accounts.models import User, BankAccountType, UserBankAccount


class UserBankAccountInterestTests(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=2
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
    
    @patch('django.utils.timezone.now')
    def test_get_monthly_interest_eligible_month(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        should_calculate, amount = self.account.get_monthly_interest()
        
        self.assertTrue(should_calculate)
        self.assertEqual(amount, Decimal('60.00'))
    
    @patch('django.utils.timezone.now')
    def test_get_monthly_interest_ineligible_month(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 2, 15, tzinfo=timezone.utc)
        
        should_calculate, amount = self.account.get_monthly_interest()
        
        self.assertFalse(should_calculate)
        self.assertEqual(amount, Decimal('0.00'))
    
    @patch('django.utils.timezone.now')
    def test_get_monthly_interest_zero_balance(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        self.account.balance = Decimal('0.00')
        
        should_calculate, amount = self.account.get_monthly_interest()
        
        self.assertFalse(should_calculate)
        self.assertEqual(amount, Decimal('0.00'))
    
    @patch('django.utils.timezone.now')
    def test_get_monthly_interest_negative_balance(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        self.account.balance = Decimal('-100.00')
        
        should_calculate, amount = self.account.get_monthly_interest()
        
        self.assertFalse(should_calculate)
        self.assertEqual(amount, Decimal('0.00'))
    
    def test_apply_interest(self):
        initial_balance = self.account.balance
        interest = Decimal('60.00')
        
        self.account.apply_interest(interest)
        
        self.assertEqual(self.account.balance, initial_balance + interest)
        self.assertEqual(self.account.balance, Decimal('1060.00'))
