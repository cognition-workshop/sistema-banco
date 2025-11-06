from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


class WithdrawFormTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('100.00')
        )

    def test_withdraw_with_sufficient_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('50.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_with_insufficient_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('150.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Saldo insuficiente', str(form.errors['amount']))

    def test_withdraw_exact_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('100.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_below_minimum_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('You can withdraw at least', str(form.errors['amount']))

    def test_withdraw_above_maximum_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('15000.00'), 'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('You can withdraw at most', str(form.errors['amount']))
