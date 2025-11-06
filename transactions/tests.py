from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.utils import process_interest_for_accounts


class ProcessInterestTestCase(TestCase):
    def setUp(self):
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
    
    def test_process_interest_for_eligible_account(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now - relativedelta(months=1)
        )
        
        result = process_interest_for_accounts(reference_date=now)
        
        self.assertEqual(result['accounts_processed'], 1)
        self.assertGreater(result['total_interest'], Decimal('0.00'))
        
        account.refresh_from_db()
        expected_interest = self.account_type.calculate_interest(Decimal('1000.00'))
        self.assertEqual(account.balance, Decimal('1000.00') + expected_interest)
        
        transactions = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST
        )
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions.first().amount, expected_interest)
    
    def test_no_interest_for_zero_balance(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('0.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now - relativedelta(months=1)
        )
        
        result = process_interest_for_accounts(reference_date=now)
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['total_interest'], Decimal('0.00'))
    
    def test_no_interest_without_initial_deposit(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=None,
            interest_start_date=None
        )
        
        result = process_interest_for_accounts(reference_date=now)
        
        self.assertEqual(result['accounts_processed'], 0)
    
    def test_interest_only_in_eligible_month(self):
        base_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.utc)
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=base_date,
            interest_start_date=timezone.datetime(2024, 6, 15, tzinfo=timezone.utc)
        )
        
        march_date = timezone.datetime(2024, 3, 15, tzinfo=timezone.utc)
        result = process_interest_for_accounts(reference_date=march_date)
        self.assertEqual(result['accounts_processed'], 0)
        
        june_date = timezone.datetime(2024, 6, 15, tzinfo=timezone.utc)
        result = process_interest_for_accounts(reference_date=june_date)
        self.assertEqual(result['accounts_processed'], 1)
    
    def test_multiple_accounts_processed(self):
        now = timezone.now()
        
        account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now - relativedelta(months=1)
        )
        
        account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now - relativedelta(months=1)
        )
        
        result = process_interest_for_accounts(reference_date=now)
        
        self.assertEqual(result['accounts_processed'], 2)
        self.assertEqual(result['transactions_created'], 2)
        
        account1.refresh_from_db()
        account2.refresh_from_db()
        self.assertGreater(account1.balance, Decimal('1000.00'))
        self.assertGreater(account2.balance, Decimal('2000.00'))
