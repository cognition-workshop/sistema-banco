from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django import forms

from accounts.models import User, BankAccountType, UserBankAccount
from accounts.constants import MALE
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


class WithdrawFormTestCase(TestCase):

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
            gender=MALE,
            balance=Decimal('4300.00')
        )

    def test_withdraw_with_sufficient_balance(self):
        form_data = {
            'amount': Decimal('4000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            account=self.account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('4000.00'))

    def test_withdraw_with_insufficient_balance(self):
        form_data = {
            'amount': Decimal('5000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            account=self.account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('Insufficient balance', form.errors['amount'][0])

    def test_withdraw_exact_balance(self):
        form_data = {
            'amount': Decimal('4300.00'),
        }
        form = WithdrawForm(
            data=form_data,
            account=self.account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('4300.00'))

    def test_withdraw_below_minimum(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = WithdrawForm(
            data=form_data,
            account=self.account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('You can withdraw at least', form.errors['amount'][0])

    def test_withdraw_above_maximum(self):
        large_account = UserBankAccount.objects.create(
            user=User.objects.create_user(
                email='test2@example.com',
                password='testpass123'
            ),
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            balance=Decimal('10000.00')
        )

        form_data = {
            'amount': Decimal('6000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            account=large_account,
            initial={'transaction_type': WITHDRAWAL}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('You can withdraw at most', form.errors['amount'][0])
