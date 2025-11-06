from decimal import Decimal
from django.test import TestCase
from django.conf import settings
from accounts.models import User, BankAccountType, UserBankAccount
from transactions.forms import WithdrawForm
from transactions.constants import WITHDRAWAL


class WithdrawFormTest(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
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
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_withdraw_with_sufficient_balance(self):
        form_data = {
            'amount': Decimal('500.00'),
        }
        form = WithdrawForm(
            data=form_data, 
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_withdraw_with_insufficient_balance(self):
        form_data = {
            'amount': Decimal('1500.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Fundos insuficientes', form.errors['amount'])
    
    def test_withdraw_exact_balance(self):
        form_data = {
            'amount': Decimal('1000.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
    
    def test_withdraw_from_zero_balance(self):
        self.account.balance = Decimal('0.00')
        self.account.save()
        
        form_data = {
            'amount': Decimal('100.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Fundos insuficientes', form.errors['amount'])
    
    def test_minimum_withdrawal_validation(self):
        form_data = {
            'amount': Decimal('5.00'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        error_message = str(form.errors['amount'])
        self.assertIn(str(settings.MINIMUM_WITHDRAWAL_AMOUNT), error_message)
    
    def test_maximum_withdrawal_validation(self):
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
        self.assertIn('amount', form.errors)
        error_message = str(form.errors['amount'])
        self.assertIn(str(self.account_type.maximum_withdrawal_amount), error_message)
    
    def test_withdraw_slightly_above_balance(self):
        form_data = {
            'amount': Decimal('1000.01'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Fundos insuficientes', form.errors['amount'])
    
    def test_withdraw_slightly_below_balance(self):
        form_data = {
            'amount': Decimal('999.99'),
        }
        form = WithdrawForm(
            data=form_data,
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
