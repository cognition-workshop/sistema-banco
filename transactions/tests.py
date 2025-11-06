from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.models import BankAccountType, UserBankAccount
from .models import Transaction
from .forms import DepositForm, WithdrawForm, TransactionDateRangeForm
from .constants import DEPOSIT, WITHDRAWAL, INTEREST
from .tasks import calculate_interest

User = get_user_model()


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
    
    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100,
            balance_after_transaction=1100,
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(str(transaction), '1000000001')


class DepositFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
    
    def test_valid_deposit(self):
        form_data = {
            'amount': 100,
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())
    
    def test_deposit_below_minimum(self):
        form_data = {
            'amount': 5,
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class WithdrawFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
    
    def test_valid_withdrawal(self):
        form_data = {
            'amount': 100,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())
    
    def test_withdrawal_below_minimum(self):
        form_data = {
            'amount': 5,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
    
    def test_withdrawal_above_maximum(self):
        form_data = {
            'amount': 10000,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
    
    def test_withdrawal_allows_negative_balance(self):
        form_data = {
            'amount': 2000,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())


class TransactionDateRangeFormTest(TestCase):
    def test_valid_date_range(self):
        form_data = {
            'date_from': '2024-01-01',
            'date_to': '2024-01-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_date_range(self):
        form_data = {
            'date_from': '2024-01-31',
            'date_to': '2024-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())


class CalculateInterestTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
    
    def test_interest_calculation_task(self):
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000,
            initial_deposit_date=date.today(),
            interest_start_date=date.today() + relativedelta(months=1)
        )
        
        initial_balance = account.balance
        calculate_interest()
        
        account.refresh_from_db()
        self.assertGreaterEqual(account.balance, initial_balance)
