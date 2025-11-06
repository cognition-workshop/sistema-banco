import pytest
from django.test import Client
from django.urls import reverse
from decimal import Decimal
from accounts.models import User, BankAccountType, UserBankAccount
from .models import Transaction
from .constants import DEPOSIT, WITHDRAWAL
from .forms import DepositForm, WithdrawForm


@pytest.mark.django_db
class TestTransactionModel:
    def test_transaction_creation(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00')
        )
        transaction = Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        assert transaction.amount == Decimal('100.00')
        assert transaction.transaction_type == DEPOSIT


@pytest.mark.django_db
class TestDepositForm:
    def setup_method(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_valid_deposit(self):
        form = DepositForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        assert form.is_valid()
    
    def test_deposit_below_minimum(self):
        form = DepositForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors


@pytest.mark.django_db
class TestWithdrawForm:
    def setup_method(self):
        user = User.objects.create_user(email='test@example.com', password='test123')
        account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=1234567890,
            gender='M',
            balance=Decimal('1000.00')
        )
    
    def test_valid_withdrawal(self):
        form = WithdrawForm(
            data={'amount': Decimal('100.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        assert form.is_valid()
    
    def test_withdrawal_exceeds_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('1500.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        assert not form.is_valid()
        assert 'amount' in form.errors
        assert 'Insufficient funds' in str(form.errors['amount'])
    
    def test_withdrawal_below_minimum(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        assert not form.is_valid()
    
    def test_withdrawal_above_maximum(self):
        form = WithdrawForm(
            data={'amount': Decimal('10000.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        assert not form.is_valid()


@pytest.mark.django_db
class TestTransactionViews:
    def test_transaction_report_view(self):
        client = Client()
        response = client.get(reverse('transactions:transaction_report'))
        assert response.status_code == 200
