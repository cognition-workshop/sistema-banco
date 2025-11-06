from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.utils import process_account_interest
from transactions.constants import INTEREST


class ProcessAccountInterestTestCase(TestCase):
    """Test cases for the process_account_interest utility function"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        self.savings_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )

        self.current_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=12
        )

    def test_interest_calculated_when_month_matches(self):
        """Test that interest is calculated when current month matches schedule"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )

        result = process_account_interest(account, 1)
        self.assertTrue(result['should_calculate'])
        self.assertGreater(result['interest_amount'], Decimal('0'))

        result = process_account_interest(account, 4)
        self.assertTrue(result['should_calculate'])
        self.assertGreater(result['interest_amount'], Decimal('0'))

    def test_no_interest_when_month_doesnt_match(self):
        """Test that interest is not calculated when month doesn't match schedule"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1000000002,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )

        result = process_account_interest(account, 2)
        self.assertFalse(result['should_calculate'])
        self.assertEqual(result['interest_amount'], Decimal('0.00'))

        result = process_account_interest(account, 5)
        self.assertFalse(result['should_calculate'])
        self.assertEqual(result['interest_amount'], Decimal('0.00'))

    def test_interest_amount_calculation(self):
        """Test that interest amount is calculated correctly"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1000000003,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )

        result = process_account_interest(account, 1)
        
        expected_interest = Decimal('12.50')
        self.assertEqual(result['interest_amount'], expected_interest)

    def test_monthly_interest_calculation(self):
        """Test monthly interest calculation (12 times per year)"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.current_type,
            account_no=1000000004,
            gender='F',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 3, 1),
            initial_deposit_date=date(2024, 3, 1)
        )

        for month in range(3, 13):
            result = process_account_interest(account, month)
            self.assertTrue(result['should_calculate'], f"Should calculate for month {month}")
            self.assertGreater(result['interest_amount'], Decimal('0'))

    def test_different_balances(self):
        """Test that interest scales with balance"""
        account1 = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1000000005,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )

        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )

        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.savings_type,
            account_no=1000000006,
            gender='M',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 15),
            initial_deposit_date=date(2024, 1, 15)
        )

        result1 = process_account_interest(account1, 1)
        result2 = process_account_interest(account2, 1)

        self.assertEqual(result2['interest_amount'], result1['interest_amount'] * 2)
