from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import DepositForm, WithdrawForm

User = get_user_model()


class TransactionFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            gender='M',
            birth_date='1990-01-01',
            account_no=1000000001,
            balance=1000
        )
    
    def test_deposit_form_minimum_amount(self):
        """Test that deposit form validates minimum amount"""
        form = DepositForm(
            data={'amount': 5},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_withdraw_form_insufficient_balance(self):
        """Test that withdraw form prevents overdraft"""
        form = WithdrawForm(
            data={'amount': 2000},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('Insufficient balance', str(form.errors['amount']))
    
    def test_withdraw_form_valid_amount(self):
        """Test that withdraw form accepts valid amounts"""
        form = WithdrawForm(
            data={'amount': 500},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())


class TransactionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='demo@example.com',
            first_name='Demo',
            last_name='User',
            password='demopass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            gender='M',
            birth_date='1990-01-01',
            account_no=1000000001,
            balance=1000
        )
    
    def test_deposit_view_accessible(self):
        """Test that deposit view is accessible"""
        response = self.client.get('/transactions/deposit/')
        self.assertEqual(response.status_code, 200)
    
    def test_withdraw_view_accessible(self):
        """Test that withdraw view is accessible"""
        response = self.client.get('/transactions/withdraw/')
        self.assertEqual(response.status_code, 200)
    
    def test_transaction_report_accessible(self):
        """Test that transaction report is accessible"""
        response = self.client.get('/transactions/report/')
        self.assertEqual(response.status_code, 200)
