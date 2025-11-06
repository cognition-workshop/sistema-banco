from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.tasks import calculate_interest


class TransactionInterestFactoryTests(TestCase):
    
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
            balance=Decimal('1060.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
    
    def test_create_interest_transaction(self):
        interest_amount = Decimal('60.00')
        balance_after = Decimal('1060.00')
        
        transaction = Transaction.create_interest_transaction(
            account=self.account,
            amount=interest_amount,
            balance_after_transaction=balance_after
        )
        
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, interest_amount)
        self.assertEqual(transaction.balance_after_transaction, balance_after)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertIsNone(transaction.pk)
        
        transaction.save()
        self.assertIsNotNone(transaction.pk)
        self.assertEqual(Transaction.objects.count(), 1)


class CalculateInterestTaskTests(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=2
        )
        
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        self.account1 = UserBankAccount.objects.create(
            user=user1,
            account_type=self.account_type,
            account_no=11111,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123'
        )
        self.account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=22222,
            gender='F',
            balance=Decimal('0.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
    
    @patch('django.utils.timezone.now')
    def test_calculate_interest_eligible_month(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        calculate_interest()
        
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        
        self.assertEqual(self.account1.balance, Decimal('1060.00'))
        self.assertEqual(self.account2.balance, Decimal('0.00'))
        
        transactions = Transaction.objects.filter(transaction_type=INTEREST)
        self.assertEqual(transactions.count(), 1)
        
        transaction = transactions.first()
        self.assertEqual(transaction.account, self.account1)
        self.assertEqual(transaction.amount, Decimal('60.00'))
        self.assertEqual(transaction.balance_after_transaction, Decimal('1060.00'))
    
    @patch('django.utils.timezone.now')
    def test_calculate_interest_ineligible_month(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 2, 15, tzinfo=timezone.utc)
        
        initial_balance = self.account1.balance
        calculate_interest()
        
        self.account1.refresh_from_db()
        self.assertEqual(self.account1.balance, initial_balance)
        
        self.assertEqual(Transaction.objects.count(), 0)
    
    @patch('django.utils.timezone.now')
    def test_calculate_interest_multiple_accounts(self, mock_now):
        mock_now.return_value = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        
        user3 = User.objects.create_user(
            email='user3@example.com',
            password='pass123'
        )
        account3 = UserBankAccount.objects.create(
            user=user3,
            account_type=self.account_type,
            account_no=33333,
            gender='M',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        calculate_interest()
        
        self.account1.refresh_from_db()
        account3.refresh_from_db()
        
        self.assertEqual(self.account1.balance, Decimal('1060.00'))
        self.assertEqual(account3.balance, Decimal('2120.00'))
        
        transactions = Transaction.objects.filter(transaction_type=INTEREST)
        self.assertEqual(transactions.count(), 2)
