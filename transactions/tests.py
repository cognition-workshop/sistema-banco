from decimal import Decimal
from django.test import TestCase
from accounts.models import User, UserBankAccount, BankAccountType
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


class WithdrawFormTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(email='test@example.com')
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=12345,
            gender='M',
            balance=Decimal('100.00')
        )
    
    def test_withdraw_insufficient_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('200.00')
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient balance', str(form.errors['amount']))
    
    def test_withdraw_sufficient_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('50.00')
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
