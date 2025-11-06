from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


User = get_user_model()


class WithdrawFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Test Savings Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdrawal_with_sufficient_balance(self):
        form_data = {
            'amount': Decimal('500.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdrawal_exceeding_balance(self):
        form_data = {
            'amount': Decimal('1500.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient funds', str(form.errors['amount']))

    def test_withdrawal_of_exact_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdrawal_leaving_zero_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['amount'], Decimal('1000.00'))

    def test_withdrawal_below_minimum_amount(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('at least', str(form.errors['amount']))

    def test_withdrawal_exceeding_maximum_amount(self):
        self.account.balance = Decimal('10000.00')
        self.account.save()
        
        form_data = {
            'amount': Decimal('6000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('at most', str(form.errors['amount']))

    def test_error_message_shows_available_balance(self):
        form_data = {
            'amount': Decimal('2000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        error_message = str(form.errors['amount'])
        self.assertIn('1000', error_message)
