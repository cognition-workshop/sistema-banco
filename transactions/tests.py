from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_for_accounts


class ProcessInterestForAccountsTests(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        now = timezone.now()
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now,
            interest_start_date=now
        )

    def test_processes_eligible_account_in_interest_month(self):
        current_month = self.account.interest_start_date.month
        
        transactions, accounts = process_interest_for_accounts(
            [self.account], current_month
        )
        
        self.assertEqual(len(transactions), 1)
        self.assertEqual(len(accounts), 1)
        
        transaction = transactions[0]
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, 0)
        self.assertEqual(
            transaction.balance_after_transaction,
            Decimal('1000.00') + transaction.amount
        )
        
        updated_account = accounts[0]
        self.assertEqual(
            updated_account.balance,
            Decimal('1000.00') + transaction.amount
        )

    def test_skips_account_not_in_interest_month(self):
        interest_months = self.account.get_interest_calculation_months()
        wrong_month = next(m for m in range(1, 13) if m not in interest_months)
        
        transactions, accounts = process_interest_for_accounts(
            [self.account], wrong_month
        )
        
        self.assertEqual(len(transactions), 0)
        self.assertEqual(len(accounts), 0)

    def test_processes_multiple_accounts(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=self.account.initial_deposit_date,
            interest_start_date=self.account.interest_start_date
        )
        
        current_month = self.account.interest_start_date.month
        
        transactions, accounts = process_interest_for_accounts(
            [self.account, account2], current_month
        )
        
        self.assertEqual(len(transactions), 2)
        self.assertEqual(len(accounts), 2)

    def test_balance_after_transaction_is_set_correctly(self):
        current_month = self.account.interest_start_date.month
        original_balance = self.account.balance
        
        transactions, accounts = process_interest_for_accounts(
            [self.account], current_month
        )
        
        transaction = transactions[0]
        expected_balance = original_balance + transaction.amount
        self.assertEqual(
            transaction.balance_after_transaction,
            expected_balance
        )
