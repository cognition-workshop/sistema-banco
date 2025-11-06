from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_interest_calculation


class ProcessInterestCalculationTests(TestCase):
    
    def setUp(self):
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
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().date()
        )
    
    def test_interest_calculation_for_eligible_account(self):
        current_month = timezone.now().month
        
        created_transactions, updated_accounts = process_interest_calculation(
            current_month=current_month
        )
        
        self.assertEqual(len(created_transactions), 1)
        self.assertEqual(len(updated_accounts), 1)
        
        transaction = created_transactions[0]
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertGreater(transaction.amount, 0)
        
        self.account.refresh_from_db()
        self.assertGreater(self.account.balance, Decimal('1000.00'))
    
    def test_no_interest_for_wrong_month(self):
        future_date = timezone.now() + relativedelta(months=2)
        self.account.interest_start_date = future_date.date()
        self.account.save()
        
        current_month = timezone.now().month
        
        created_transactions, updated_accounts = process_interest_calculation(
            current_month=current_month
        )
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_no_interest_for_zero_balance(self):
        self.account.balance = Decimal('0.00')
        self.account.save()
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_no_interest_without_initial_deposit(self):
        self.account.initial_deposit_date = None
        self.account.save()
        
        created_transactions, updated_accounts = process_interest_calculation()
        
        self.assertEqual(len(created_transactions), 0)
        self.assertEqual(len(updated_accounts), 0)
    
    def test_multiple_accounts_processing(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=1002,
            gender='F',
            birth_date=date(1992, 1, 1),
            balance=Decimal('2000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().date()
        )
        
        current_month = timezone.now().month
        
        created_transactions, updated_accounts = process_interest_calculation(
            current_month=current_month
        )
        
        self.assertEqual(len(created_transactions), 2)
        self.assertEqual(len(updated_accounts), 2)
        
        self.account.refresh_from_db()
        account2.refresh_from_db()
        self.assertGreater(self.account.balance, Decimal('1000.00'))
        self.assertGreater(account2.balance, Decimal('2000.00'))
    
    def test_custom_queryset_parameter(self):
        custom_queryset = UserBankAccount.objects.filter(
            account_no=self.account.account_no
        ).select_related('account_type')
        
        current_month = timezone.now().month
        
        created_transactions, updated_accounts = process_interest_calculation(
            accounts_queryset=custom_queryset,
            current_month=current_month
        )
        
        self.assertEqual(len(created_transactions), 1)
        self.assertEqual(created_transactions[0].account, self.account)
    
    def test_transaction_balance_after_transaction_field(self):
        current_month = timezone.now().month
        original_balance = self.account.balance
        
        created_transactions, updated_accounts = process_interest_calculation(
            current_month=current_month
        )
        
        self.assertEqual(len(created_transactions), 1)
        transaction = created_transactions[0]
        
        expected_balance = original_balance + transaction.amount
        self.assertEqual(transaction.balance_after_transaction, expected_balance)
