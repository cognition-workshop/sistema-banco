from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.utils import timezone
from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.utils import process_interest_for_accounts


class ProcessInterestForAccountsTestCase(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
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
            account_no=1000001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )
    
    def test_processes_eligible_account(self):
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['accounts_updated'], 1)
        self.assertEqual(result['transactions_created'], 1)
        self.assertGreater(result['total_interest'], Decimal('0'))
        
        self.account.refresh_from_db()
        self.assertGreater(self.account.balance, Decimal('1000.00'))
        
        transaction = Transaction.objects.get(account=self.account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(transaction.amount, result['total_interest'])
        self.assertEqual(transaction.balance_after_transaction, self.account.balance)
    
    def test_skips_wrong_month(self):
        self.account.interest_start_date = date(2024, 2, 1)
        self.account.save()
        
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['accounts_updated'], 0)
        self.assertEqual(result['transactions_created'], 0)
        self.assertEqual(result['total_interest'], Decimal('0.00'))
    
    def test_skips_zero_balance(self):
        self.account.balance = Decimal('0.00')
        self.account.save()
        
        result = process_interest_for_accounts()
        
        self.assertEqual(result['accounts_updated'], 0)
        self.assertEqual(result['transactions_created'], 0)
    
    def test_skips_future_interest_start_date(self):
        future_date = date(2025, 12, 31)
        self.account.interest_start_date = future_date
        self.account.save()
        
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['accounts_updated'], 0)
        self.assertEqual(result['transactions_created'], 0)
    
    def test_skips_no_initial_deposit(self):
        self.account.initial_deposit_date = None
        self.account.save()
        
        result = process_interest_for_accounts()
        
        self.assertEqual(result['accounts_updated'], 0)
    
    def test_processes_multiple_accounts(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=1000002,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )
        
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['accounts_updated'], 2)
        self.assertEqual(result['transactions_created'], 2)
        
        self.account.refresh_from_db()
        account2.refresh_from_db()
        self.assertGreater(self.account.balance, Decimal('1000.00'))
        self.assertGreater(account2.balance, Decimal('2000.00'))
        
        transactions = Transaction.objects.filter(transaction_type=INTEREST)
        self.assertEqual(transactions.count(), 2)
    
    def test_no_eligible_accounts(self):
        self.account.delete()
        
        result = process_interest_for_accounts()
        
        self.assertEqual(result['accounts_updated'], 0)
        self.assertEqual(result['transactions_created'], 0)
        self.assertEqual(result['total_interest'], Decimal('0.00'))
    
    def test_different_interest_calculation_frequencies(self):
        quarterly_account_type = BankAccountType.objects.create(
            name='Quarterly Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('8.00'),
            interest_calculation_per_year=4
        )
        
        user2 = User.objects.create_user(
            email='quarterly@example.com',
            password='testpass123'
        )
        
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=quarterly_account_type,
            account_no=1000003,
            gender='F',
            balance=Decimal('5000.00'),
            initial_deposit_date=date(2024, 1, 1),
            interest_start_date=date(2024, 1, 1)
        )
        
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['accounts_updated'], 2)
        
        account2.refresh_from_db()
        self.assertGreater(account2.balance, Decimal('5000.00'))
    
    def test_interest_calculation_accuracy(self):
        expected_interest = self.account.account_type.calculate_interest(
            self.account.balance
        )
        
        test_date = timezone.datetime(2024, 1, 15, tzinfo=timezone.get_current_timezone())
        
        result = process_interest_for_accounts(current_date=test_date)
        
        self.assertEqual(result['total_interest'], expected_interest)
        
        self.account.refresh_from_db()
        expected_balance = Decimal('1000.00') + expected_interest
        self.assertEqual(self.account.balance, expected_balance)
