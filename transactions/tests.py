from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.forms import WithdrawForm, DepositForm
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class WithdrawalValidationTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000.00
        )
    
    def test_withdraw_more_than_balance(self):
        form_data = {
            'amount': 1500.00,
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient funds', str(form.errors))
    
    def test_withdraw_valid_amount(self):
        form_data = {
            'amount': 500.00,
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_withdraw_exactly_balance(self):
        form_data = {
            'amount': 1000.00,
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())


class DepositValidationTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=0.00
        )
    
    def test_deposit_below_minimum(self):
        form_data = {
            'amount': 5.00,
        }
        form = DepositForm(
            data=form_data,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('at least', str(form.errors).lower())
    
    def test_deposit_valid_amount(self):
        form_data = {
            'amount': 100.00,
        }
        form = DepositForm(
            data=form_data,
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
