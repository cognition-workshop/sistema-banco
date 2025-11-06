from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_calculation


class InterestCalculationUtilityTest(TestCase):
    """Test the process_interest_calculation utility function"""

    def setUp(self):
        """Set up test data"""
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=12
        )

        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123'
        )

        current_date = timezone.now().date()
        self.account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=current_date - relativedelta(months=1),
            interest_start_date=current_date
        )

        next_month = current_date + relativedelta(months=1)
        self.account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.account_type,
            account_no=1000002,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=current_date - relativedelta(months=1),
            interest_start_date=next_month
        )

    def test_interest_calculation_for_eligible_account(self):
        """Test that interest is calculated and applied for eligible accounts"""
        initial_balance = self.account1.balance
        
        result = process_interest_calculation()
        
        self.account1.refresh_from_db()
        
        self.assertGreater(self.account1.balance, initial_balance)
        
        self.assertEqual(result['accounts_processed'], 1)
        self.assertGreater(result['total_interest'], 0)
        
        transactions = Transaction.objects.filter(
            account=self.account1,
            transaction_type=INTEREST
        )
        self.assertEqual(transactions.count(), 1)
        self.assertGreater(transactions.first().amount, 0)

    def test_no_interest_for_wrong_month(self):
        """Test that accounts in non-interest months don't receive interest"""
        initial_balance = self.account2.balance
        
        result = process_interest_calculation()
        
        self.account2.refresh_from_db()
        
        self.assertEqual(self.account2.balance, initial_balance)
        
        transactions = Transaction.objects.filter(
            account=self.account2,
            transaction_type=INTEREST
        )
        self.assertEqual(transactions.count(), 0)

    def test_no_interest_for_zero_balance(self):
        """Test that accounts with zero or negative balance don't receive interest"""
        self.account1.balance = Decimal('0.00')
        self.account1.save()
        
        result = process_interest_calculation()
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['total_interest'], 0)

    def test_no_interest_without_initial_deposit(self):
        """Test that accounts without initial deposit date don't receive interest"""
        self.account1.initial_deposit_date = None
        self.account1.save()
        
        result = process_interest_calculation()
        
        self.assertEqual(result['accounts_processed'], 0)

    def test_multiple_accounts_processed(self):
        """Test processing multiple eligible accounts at once"""
        current_date = timezone.now().date()
        self.account2.interest_start_date = current_date
        self.account2.save()
        
        initial_balance1 = self.account1.balance
        initial_balance2 = self.account2.balance
        
        result = process_interest_calculation()
        
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        
        self.assertGreater(self.account1.balance, initial_balance1)
        self.assertGreater(self.account2.balance, initial_balance2)
        
        self.assertEqual(result['accounts_processed'], 2)
        
        total_transactions = Transaction.objects.filter(
            transaction_type=INTEREST
        ).count()
        self.assertEqual(total_transactions, 2)

    def test_interest_calculation_accuracy(self):
        """Test that interest is calculated with correct formula"""
        self.account1.balance = Decimal('1000.00')
        self.account1.save()
        
        expected_interest = Decimal('10.00')
        
        result = process_interest_calculation()
        
        self.account1.refresh_from_db()
        
        self.assertEqual(
            self.account1.balance,
            Decimal('1000.00') + expected_interest
        )
