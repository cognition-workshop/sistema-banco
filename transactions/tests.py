from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_calculation


class InterestCalculationTestCase(TestCase):
    """Test cases for the interest calculation utility function."""
    
    def setUp(self):
        """Set up test data."""
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_interest_calculation_for_eligible_account(self):
        """Test that interest is calculated for an eligible account."""
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=123456,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - timedelta(days=60),
            interest_start_date=now - timedelta(days=1)
        )
        
        initial_balance = account.balance
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 1)
        self.assertEqual(created_transactions[0].account, account)
        self.assertEqual(created_transactions[0].transaction_type, INTEREST)
        self.assertGreater(created_transactions[0].amount, 0)
        
        self.assertEqual(len(updated_accounts), 1)
        account.refresh_from_db()
        self.assertGreater(account.balance, initial_balance)
    
    def test_no_interest_for_zero_balance_account(self):
        """Test that no interest is calculated for accounts with zero balance."""
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=123457,
            gender='M',
            balance=Decimal('0.00'),
            initial_deposit_date=now - timedelta(days=60),
            interest_start_date=now - timedelta(days=1)
        )
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_no_interest_for_future_interest_start_date(self):
        """Test that no interest is calculated if interest_start_date is in the future."""
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=123458,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - timedelta(days=60),
            interest_start_date=now + timedelta(days=30)
        )
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_no_interest_without_initial_deposit_date(self):
        """Test that no interest is calculated if initial_deposit_date is not set."""
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=123459,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=None,
            interest_start_date=now - timedelta(days=1)
        )
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
