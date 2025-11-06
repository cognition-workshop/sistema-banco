from decimal import Decimal
from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_monthly_interest


class ProcessMonthlyInterestTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('12.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_no_eligible_accounts(self):
        now = timezone.make_aware(datetime(2024, 1, 1))
        result = process_monthly_interest(now=now)
        
        self.assertEqual(len(result['accounts_processed']), 0)
        self.assertEqual(len(result['transactions_created']), 0)
    
    def test_account_with_zero_balance_skipped(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=Decimal('0.00'),
            initial_deposit_date=timezone.make_aware(datetime(2024, 1, 1)),
            interest_start_date=timezone.make_aware(datetime(2024, 1, 1))
        )
        
        now = timezone.make_aware(datetime(2024, 1, 15))
        result = process_monthly_interest(now=now)
        
        self.assertEqual(len(result['accounts_processed']), 0)
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('0.00'))
    
    def test_account_future_interest_start_date_skipped(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.make_aware(datetime(2024, 1, 1)),
            interest_start_date=timezone.make_aware(datetime(2024, 2, 1))
        )
        
        now = timezone.make_aware(datetime(2024, 1, 15))
        result = process_monthly_interest(now=now)
        
        self.assertEqual(len(result['accounts_processed']), 0)
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('1000.00'))
    
    def test_single_account_interest_calculation(self):
        initial_balance = Decimal('1000.00')
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=initial_balance,
            initial_deposit_date=timezone.make_aware(datetime(2024, 1, 1)),
            interest_start_date=timezone.make_aware(datetime(2024, 1, 1))
        )
        
        now = timezone.make_aware(datetime(2024, 1, 15))
        result = process_monthly_interest(now=now)
        
        self.assertEqual(len(result['accounts_processed']), 1)
        self.assertEqual(len(result['transactions_created']), 1)
        
        account.refresh_from_db()
        expected_interest = self.account_type.calculate_interest(initial_balance)
        expected_balance = initial_balance + expected_interest
        self.assertEqual(account.balance, expected_balance)
        
        transaction = Transaction.objects.get(account=account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(transaction.amount, expected_interest)
        self.assertEqual(transaction.balance_after_transaction, expected_balance)
    
    def test_multiple_accounts_processed(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        account1 = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.make_aware(datetime(2024, 1, 1)),
            interest_start_date=timezone.make_aware(datetime(2024, 1, 1))
        )
        
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=12346,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=timezone.make_aware(datetime(2024, 1, 1)),
            interest_start_date=timezone.make_aware(datetime(2024, 1, 1))
        )
        
        now = timezone.make_aware(datetime(2024, 1, 15))
        result = process_monthly_interest(now=now)
        
        self.assertEqual(len(result['accounts_processed']), 2)
        self.assertEqual(len(result['transactions_created']), 2)
        
        self.assertEqual(Transaction.objects.filter(transaction_type=INTEREST).count(), 2)
