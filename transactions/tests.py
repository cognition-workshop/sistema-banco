from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import calculate_interest_for_accounts


class CalculateInterestForAccountsTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=4
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_calculate_interest_for_eligible_account(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - relativedelta(months=4),
            interest_start_date=now - relativedelta(months=3)
        )
        
        transactions_created, accounts_updated = calculate_interest_for_accounts()
        
        self.assertEqual(transactions_created, 1)
        self.assertEqual(accounts_updated, 1)
        
        account.refresh_from_db()
        expected_interest = self.account_type.calculate_interest(Decimal('1000.00'))
        self.assertEqual(account.balance, Decimal('1000.00') + expected_interest)
        
        transaction = Transaction.objects.get(account=account, transaction_type=INTEREST)
        self.assertEqual(transaction.amount, expected_interest)
        self.assertEqual(transaction.balance_after_transaction, account.balance)
    
    def test_no_interest_for_zero_balance(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000002,
            gender='M',
            balance=Decimal('0.00'),
            initial_deposit_date=now - relativedelta(months=4),
            interest_start_date=now - relativedelta(months=3)
        )
        
        transactions_created, accounts_updated = calculate_interest_for_accounts()
        
        self.assertEqual(transactions_created, 0)
        self.assertEqual(accounts_updated, 0)
    
    def test_no_interest_without_initial_deposit(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000003,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=None,
            interest_start_date=None
        )
        
        transactions_created, accounts_updated = calculate_interest_for_accounts()
        
        self.assertEqual(transactions_created, 0)
        self.assertEqual(accounts_updated, 0)
    
    def test_no_interest_before_start_date(self):
        now = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000004,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now,
            interest_start_date=now + relativedelta(months=3)
        )
        
        transactions_created, accounts_updated = calculate_interest_for_accounts()
        
        self.assertEqual(transactions_created, 0)
        self.assertEqual(accounts_updated, 0)
