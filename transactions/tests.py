from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import BankAccountType, UserBankAccount
from transactions.forms import DepositForm, WithdrawForm
from transactions.constants import DEPOSIT, WITHDRAWAL


User = get_user_model()


class TransactionFormValidationTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_deposit_minimum_amount(self):
        form = DepositForm(
            data={'amount': Decimal('5.00'), 'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_deposit_negative_amount(self):
        form = DepositForm(
            data={'amount': Decimal('-10.00'), 'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
    
    def test_deposit_zero_amount(self):
        form = DepositForm(
            data={'amount': Decimal('0.00'), 'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())
    
    def test_deposit_valid_amount(self):
        form = DepositForm(
            data={'amount': Decimal('100.00'), 'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_withdraw_insufficient_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('2000.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('Saldo insuficiente', str(form.errors['amount']))
    
    def test_withdraw_exceeds_maximum(self):
        self.account.balance = Decimal('10000.00')
        self.account.save()
        
        form = WithdrawForm(
            data={'amount': Decimal('6000.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_withdraw_below_minimum(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
    
    def test_withdraw_valid_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('100.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
