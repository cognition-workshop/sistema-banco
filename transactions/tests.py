from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.forms import ValidationError

from accounts.models import UserBankAccount, BankAccountType
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


User = get_user_model()


class WithdrawFormTestCase(TestCase):

    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdraw_with_sufficient_balance(self):
        form_data = {
            'amount': Decimal('500.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('500.00'))

    def test_withdraw_exceeding_balance(self):
        form_data = {
            'amount': Decimal('1500.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('cannot withdraw more than your balance', str(form.errors['amount']).lower())

    def test_withdraw_equal_to_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('1000.00'))

    def test_withdraw_with_zero_balance(self):
        self.account.balance = Decimal('0.00')
        self.account.save()
        
        form_data = {
            'amount': Decimal('50.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_withdraw_minimum_amount_validation_still_works(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('at least', str(form.errors['amount']).lower())

    def test_withdraw_maximum_amount_validation_still_works(self):
        self.account.balance = Decimal('20000.00')
        self.account.save()
        
        form_data = {
            'amount': Decimal('15000.00'),
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('at most', str(form.errors['amount']).lower())
