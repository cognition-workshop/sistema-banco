from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, UserBankAccount, BankAccountType
from accounts.utils import process_interest_calculation
from transactions.models import Transaction
from transactions.constants import INTEREST


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
        
        now = timezone.now()
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=123456,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now
        )
    
    def test_process_interest_calculation_basic(self):
        result = process_interest_calculation()
        
        self.assertEqual(result['accounts_processed'], 1)
        self.assertGreater(result['total_interest'], Decimal('0'))
        self.assertEqual(result['transactions_created'], 1)
        
        self.account.refresh_from_db()
        self.assertGreater(self.account.balance, Decimal('1000.00'))
        
        transaction = Transaction.objects.filter(
            account=self.account,
            transaction_type=INTEREST
        ).first()
        self.assertIsNotNone(transaction)
        self.assertGreater(transaction.amount, Decimal('0'))
    
    def test_process_interest_calculation_no_eligible_accounts(self):
        self.account.balance = Decimal('0')
        self.account.save()
        
        result = process_interest_calculation()
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['total_interest'], Decimal('0'))
        self.assertEqual(result['transactions_created'], 0)
    
    def test_process_interest_calculation_with_custom_queryset(self):
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        now = timezone.now()
        account2 = UserBankAccount.objects.create(
            user=user2,
            account_type=self.account_type,
            account_no=654321,
            gender='F',
            balance=Decimal('2000.00'),
            initial_deposit_date=now - relativedelta(months=2),
            interest_start_date=now
        )
        
        queryset = UserBankAccount.objects.filter(account_no=654321)
        result = process_interest_calculation(accounts_queryset=queryset)
        
        self.assertEqual(result['accounts_processed'], 1)
        
        account2.refresh_from_db()
        self.assertGreater(account2.balance, Decimal('2000.00'))
    
    def test_process_interest_calculation_wrong_month(self):
        self.account.interest_start_date = timezone.now() + relativedelta(months=1)
        self.account.save()
        
        result = process_interest_calculation()
        
        self.assertEqual(result['accounts_processed'], 0)
        self.assertEqual(result['total_interest'], Decimal('0'))
