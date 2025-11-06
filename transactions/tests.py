from django.test import TestCase
from django.conf import settings
from decimal import Decimal

from accounts.models import User, UserBankAccount, BankAccountType
from transactions.forms import WithdrawForm, DepositForm
from transactions.constants import WITHDRAWAL, DEPOSIT


class WithdrawFormBalanceValidationTest(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=settings.ACCOUNT_NUMBER_START_FROM,
            gender='M',
            balance=Decimal('500.00')
        )
    
    def test_withdraw_within_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('300.00'),
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertTrue(form.is_valid())
    
    def test_withdraw_exceeds_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('600.00'),
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('insufficient balance', str(form.errors['amount']).lower())
    
    def test_withdraw_exact_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('500.00'),
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertTrue(form.is_valid())
    
    def test_withdraw_minimum_amount(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('5.00'),
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
