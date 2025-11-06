from decimal import Decimal
from datetime import datetime, date
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.utils import process_interest_calculation


class InterestCalculationTests(TestCase):
    
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
    
    def test_calculates_interest_for_eligible_account(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        test_time = timezone.make_aware(datetime(2024, 2, 1))
        
        result = process_interest_calculation(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 1)
        self.assertGreater(result['total_interest'], Decimal('0.00'))
        self.assertEqual(result['transactions_created'], 1)
        
        account.refresh_from_db()
        self.assertGreater(account.balance, Decimal('1000.00'))
        
        transaction = Transaction.objects.get(account=account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(transaction.amount, result['total_interest'])
    
    def test_skips_account_with_zero_balance(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1002,
            gender='F',
            birth_date=date(1985, 5, 10),
            balance=Decimal('0.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        test_time = timezone.make_aware(datetime(2024, 2, 1))
        result = process_interest_calculation(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['total_interest'], Decimal('0.00'))
        self.assertEqual(result['transactions_created'], 0)
    
    def test_skips_account_without_initial_deposit(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1003,
            gender='M',
            birth_date=date(1992, 3, 20),
            balance=Decimal('500.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=None
        )
        
        test_time = timezone.make_aware(datetime(2024, 2, 1))
        result = process_interest_calculation(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 0)
    
    def test_processes_multiple_accounts(self):
        for i in range(3):
            UserBankAccount.objects.create(
                user=User.objects.create_user(
                    email=f'test{i}@example.com',
                    password='testpass123'
                ),
                account_type=self.account_type,
                account_no=2000 + i,
                gender='M',
                birth_date=date(1990, 1, 1),
                balance=Decimal('1000.00'),
                interest_start_date=date(2024, 1, 1),
                initial_deposit_date=date(2024, 1, 15)
            )
        
        test_time = timezone.make_aware(datetime(2024, 2, 1))
        result = process_interest_calculation(current_time=test_time)
        
        self.assertEqual(result['accounts_processed'], 3)
        self.assertEqual(result['transactions_created'], 3)
        self.assertEqual(Transaction.objects.filter(transaction_type=INTEREST).count(), 3)
    
    def test_returns_correct_statistics(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=3001,
            gender='F',
            birth_date=date(1988, 8, 5),
            balance=Decimal('5000.00'),
            interest_start_date=date(2024, 1, 1),
            initial_deposit_date=date(2024, 1, 15)
        )
        
        test_time = timezone.make_aware(datetime(2024, 2, 1))
        result = process_interest_calculation(current_time=test_time)
        
        self.assertIn('accounts_processed', result)
        self.assertIn('total_interest', result)
        self.assertIn('transactions_created', result)
        self.assertIsInstance(result['total_interest'], Decimal)
