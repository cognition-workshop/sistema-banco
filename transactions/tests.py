from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import INTEREST
from transactions.utils import apply_monthly_interest


class ApplyMonthlyInterestTestCase(TestCase):
    """Test cases for the apply_monthly_interest utility function."""
    
    def setUp(self):
        """Set up test data."""
        self.savings_type = BankAccountType.objects.create(
            name="Savings Account",
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.00,
            interest_calculation_per_year=12
        )
        
        self.current_type = BankAccountType.objects.create(
            name="Current Account",
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=2.50,
            interest_calculation_per_year=2
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_apply_interest_to_eligible_account(self):
        """Test that interest is correctly applied to an eligible account."""
        current_date = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1001,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=current_date - relativedelta(months=2),
            interest_start_date=current_date - relativedelta(months=1)
        )
        
        initial_balance = account.balance
        
        result = apply_monthly_interest(current_month=current_date.month)
        
        account.refresh_from_db()
        
        self.assertGreater(account.balance, initial_balance)
        
        self.assertEqual(result['transactions_created'], 1)
        self.assertEqual(result['accounts_updated'], 1)
        self.assertGreater(result['total_interest'], 0)
        
        transaction = Transaction.objects.get(account=account)
        self.assertEqual(transaction.transaction_type, INTEREST)
        self.assertEqual(transaction.amount, result['total_interest'])
        self.assertEqual(transaction.balance_after_transaction, account.balance)
    
    def test_no_interest_for_zero_balance(self):
        """Test that accounts with zero balance don't receive interest."""
        current_date = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1002,
            gender='F',
            balance=Decimal('0.00'),
            initial_deposit_date=current_date - relativedelta(months=2),
            interest_start_date=current_date - relativedelta(months=1)
        )
        
        result = apply_monthly_interest(current_month=current_date.month)
        
        self.assertEqual(result['transactions_created'], 0)
        self.assertEqual(result['accounts_updated'], 0)
        self.assertEqual(result['total_interest'], 0)
    
    def test_no_interest_for_future_interest_start_date(self):
        """Test that accounts with future interest start dates don't receive interest."""
        current_date = timezone.now()
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1003,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=current_date - relativedelta(months=2),
            interest_start_date=current_date + relativedelta(months=1)
        )
        
        result = apply_monthly_interest(current_month=current_date.month)
        
        self.assertEqual(result['transactions_created'], 0)
        self.assertEqual(result['accounts_updated'], 0)
    
    def test_interest_only_on_calculation_months(self):
        """Test that interest is only applied on designated calculation months."""
        current_date = timezone.now()
        
        interest_start = current_date.replace(month=1, day=1)
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.current_type,
            account_no=1004,
            gender='M',
            balance=Decimal('1000.00'),
            initial_deposit_date=interest_start - relativedelta(months=1),
            interest_start_date=interest_start
        )
        
        result_jan = apply_monthly_interest(current_month=1)
        self.assertGreater(result_jan['transactions_created'], 0)
        
        Transaction.objects.all().delete()
        
        result_feb = apply_monthly_interest(current_month=2)
        self.assertEqual(result_feb['transactions_created'], 0)
        
        result_jul = apply_monthly_interest(current_month=7)
        self.assertGreater(result_jul['transactions_created'], 0)
    
    def test_multiple_accounts_bulk_processing(self):
        """Test that multiple accounts are processed efficiently in bulk."""
        current_date = timezone.now()
        
        accounts = []
        for i in range(5):
            user = User.objects.create_user(
                email=f'test{i}@example.com',
                password='testpass123'
            )
            account = UserBankAccount.objects.create(
                user=user,
                account_type=self.savings_type,
                account_no=2000 + i,
                gender='M',
                balance=Decimal('1000.00'),
                initial_deposit_date=current_date - relativedelta(months=2),
                interest_start_date=current_date - relativedelta(months=1)
            )
            accounts.append(account)
        
        result = apply_monthly_interest(current_month=current_date.month)
        
        self.assertEqual(result['transactions_created'], 5)
        self.assertEqual(result['accounts_updated'], 5)
        self.assertGreater(result['total_interest'], 0)
        
        self.assertEqual(Transaction.objects.filter(transaction_type=INTEREST).count(), 5)
    
    def test_interest_calculation_accuracy(self):
        """Test that the calculated interest amount is accurate."""
        current_date = timezone.now()
        balance = Decimal('1000.00')
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.savings_type,
            account_no=1005,
            gender='M',
            balance=balance,
            initial_deposit_date=current_date - relativedelta(months=2),
            interest_start_date=current_date - relativedelta(months=1)
        )
        
        expected_interest = balance * (Decimal('1') + (Decimal('5.00') / Decimal('100')) / Decimal('12')) - balance
        expected_interest = round(expected_interest, 2)
        
        result = apply_monthly_interest(current_month=current_date.month)
        
        self.assertEqual(result['total_interest'], expected_interest)
