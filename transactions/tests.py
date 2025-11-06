from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from transactions.utils import process_monthly_interest


class ProcessMonthlyInterestTestCase(TestCase):
    
    def setUp(self):
        self.savings_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.current_type = BankAccountType.objects.create(
            name='Current',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('3.00'),
            interest_calculation_per_year=4
        )
        
        self.user1 = User.objects.create_user(
            email='test1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        self.user3 = User.objects.create_user(
            email='test3@example.com',
            password='testpass123'
        )
    
    def test_process_interest_for_eligible_account(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 1, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 1)
        self.assertEqual(result['transactions_created'], 1)
        self.assertGreater(result['total_interest_paid'], Decimal('0'))
        
        account.refresh_from_db()
        expected_interest = self.savings_type.calculate_interest(Decimal('1000.00'))
        self.assertEqual(account.balance, Decimal('1000.00') + expected_interest)
        
        transaction = Transaction.objects.get(account=account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(transaction.amount, expected_interest)
        self.assertEqual(transaction.balance_after_transaction, account.balance)
    
    def test_skip_account_in_wrong_month(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.current_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('5000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 2, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['transactions_created'], 0)
        self.assertEqual(result['total_interest_paid'], Decimal('0.00'))
        
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('5000.00'))
        
        self.assertEqual(Transaction.objects.filter(account=account).count(), 0)
    
    def test_skip_account_with_zero_balance(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('0.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 1, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['transactions_created'], 0)
    
    def test_skip_account_without_interest_start_date(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=None,
            initial_deposit_date=date(2024, 1, 1)
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 1, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
    
    def test_skip_account_without_initial_deposit_date(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=None
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 1, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
    
    def test_process_multiple_accounts(self):
        account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.savings_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('2000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        account3 = UserBankAccount.objects.create(
            user=self.user3,
            account_type=self.savings_type,
            account_no=1000000003,
            gender='M',
            balance=Decimal('0.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 1)
        )
        
        test_time = timezone.make_aware(timezone.datetime(2024, 1, 15))
        result = process_monthly_interest(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 2)
        self.assertEqual(result['transactions_created'], 2)
        
        account1.refresh_from_db()
        account2.refresh_from_db()
        self.assertGreater(account1.balance, Decimal('1000.00'))
        self.assertGreater(account2.balance, Decimal('2000.00'))
        
        self.assertEqual(Transaction.objects.filter(account=account1).count(), 1)
        self.assertEqual(Transaction.objects.filter(account=account2).count(), 1)
        self.assertEqual(Transaction.objects.filter(account=account3).count(), 0)
    
    def test_uses_current_time_if_not_provided(self):
        account = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.savings_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00'),
            interest_start_date=date.today().replace(day=1),
            initial_deposit_date=date.today()
        )
        
        result = process_monthly_interest()
        
        current_month = timezone.now().month
        if current_month in account.get_interest_calculation_months():
            self.assertEqual(result['accounts_processed'], 1)
        else:
            self.assertEqual(result['accounts_processed'], 0)
