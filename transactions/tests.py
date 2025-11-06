from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import date

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_account_interest


class ProcessAccountInterestTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=12
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
    
    def test_calculates_interest_when_month_matches(self):
        updated_account, transaction = process_account_interest(self.account, 1)
        
        self.assertIsNotNone(updated_account)
        self.assertIsNotNone(transaction)
        
        expected_interest = Decimal('10.00')
        self.assertEqual(transaction.amount, expected_interest)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(updated_account.balance, Decimal('1010.00'))
        self.assertEqual(transaction.balance_after_transaction, Decimal('1010.00'))
    
    def test_no_interest_when_month_does_not_match(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 2, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        updated_account, transaction = process_account_interest(account2, 1)
        
        self.assertIsNone(updated_account)
        self.assertIsNone(transaction)
    
    def test_interest_calculation_with_different_rates(self):
        user3 = User.objects.create_user(
            email='test3@example.com',
            password='testpass123'
        )
        
        quarterly_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('8.00'),
            interest_calculation_per_year=4
        )
        
        account3 = UserBankAccount.objects.create(
            user=user3,
            account_type=quarterly_type,
            account_no=1000000003,
            gender='M',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        updated_account, transaction = process_account_interest(account3, 1)
        
        self.assertIsNotNone(updated_account)
        expected_interest = Decimal('40.00')
        self.assertEqual(transaction.amount, expected_interest)
    
    def test_transaction_fields_are_correct(self):
        updated_account, transaction = process_account_interest(self.account, 1)
        
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, 0)
        self.assertEqual(
            transaction.balance_after_transaction,
            self.account.balance
        )
