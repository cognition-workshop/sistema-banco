from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.utils import process_account_interest


class ProcessAccountInterestTests(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        now = timezone.now()
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now,
            interest_start_date=now
        )

    def test_process_account_interest_calculates_when_month_matches(self):
        """Test that interest is calculated when current month matches."""
        current_month = self.account.interest_start_date.month
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.transaction_type, INTEREST)
        self.assertGreater(transaction_obj.amount, Decimal('0'))
        self.assertEqual(
            updated_account.balance,
            Decimal('1000.00') + transaction_obj.amount
        )

    def test_process_account_interest_skips_when_month_doesnt_match(self):
        """Test that interest is not calculated when month doesn't match."""
        current_month = (self.account.interest_start_date.month + 1) % 12
        if current_month == 0:
            current_month = 12
        
        if current_month in self.account.get_interest_calculation_months():
            current_month = (current_month + 1) % 12
            if current_month == 0:
                current_month = 12
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertIsNone(updated_account)
        self.assertIsNone(transaction_obj)

    def test_process_account_interest_uses_correct_interest_rate(self):
        """Test that interest is calculated using the correct rate."""
        current_month = self.account.interest_start_date.month
        
        expected_interest = self.account.account_type.calculate_interest(
            self.account.balance
        )
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertEqual(transaction_obj.amount, expected_interest)

    def test_process_account_interest_with_zero_balance(self):
        """Test behavior with zero balance."""
        self.account.balance = Decimal('0.00')
        current_month = self.account.interest_start_date.month
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(transaction_obj)
        self.assertEqual(transaction_obj.amount, Decimal('0.00'))

    def test_process_account_interest_with_high_balance(self):
        """Test interest calculation with high balance."""
        self.account.balance = Decimal('100000.00')
        current_month = self.account.interest_start_date.month
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(transaction_obj)
        self.assertGreater(transaction_obj.amount, Decimal('0'))

    def test_process_account_interest_quarterly_calculation(self):
        """Test interest calculation for quarterly frequency."""
        self.account_type.interest_calculation_per_year = 4
        self.account_type.save()
        
        current_month = self.account.interest_start_date.month
        
        updated_account, transaction_obj = process_account_interest(
            self.account, current_month
        )
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(transaction_obj)
