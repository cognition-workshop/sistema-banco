from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL

User = get_user_model()


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
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdraw_with_sufficient_balance(self):
        form_data = {
            'amount': Decimal('500.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())

    def test_withdraw_exceeds_balance(self):
        form_data = {
            'amount': Decimal('1500.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('Saldo insuficiente', str(form.errors['amount']))

    def test_withdraw_exact_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertTrue(form.is_valid())

    def test_withdraw_zero_balance_account(self):
        self.account.balance = Decimal('0.00')
        self.account.save()
        
        form_data = {
            'amount': Decimal('10.00'),
            'transaction_type': WITHDRAWAL
        }
        form = WithdrawForm(data=form_data, account=self.account)
        self.assertFalse(form.is_valid())
        self.assertIn('Saldo insuficiente', str(form.errors['amount']))
