from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.models import BankAccountType, UserBankAccount
from accounts.utils import validate_brazilian_account
from .models import Transaction
from .forms import DepositForm, WithdrawForm, TransactionDateRangeForm
from .constants import DEPOSIT, WITHDRAWAL, INTEREST
from .tasks import calculate_interest

User = get_user_model()


class TransactionAtomicityTests(TestCase):
    """Test that all balance operations are atomic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )

        agencia = 1
        conta = 2000
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_deposit_is_atomic(self):
        """Test that deposits are atomic transactions."""
        initial_balance = self.account.balance

        form = DepositForm(
            data={"amount": Decimal("100.00")},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )

        if not form.is_valid():
            self.fail(f"Form validation failed: {form.errors}")

        form.save()

        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, initial_balance + Decimal("100.00"))

        self.assertEqual(Transaction.objects.count(), 1)

    def test_withdraw_validates_balance(self):
        """Test that withdrawals validate sufficient balance."""
        form = WithdrawForm(
            data={"amount": Decimal("2000.00")},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_withdraw_is_atomic(self):
        """Test that withdrawals are atomic transactions."""
        initial_balance = self.account.balance

        form = WithdrawForm(
            data={"amount": Decimal("100.00")},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )

        if not form.is_valid():
            self.fail(f"Form validation failed: {form.errors}")

        form.save()

        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, initial_balance - Decimal("100.00"))


class ValidationTests(TestCase):
    """Test validation logic."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        self.account_type = BankAccountType.objects.create(
            name="Savings",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("5.00"),
            interest_calculation_per_year=12,
        )

        agencia = 1
        conta = 2001
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_negative_amount_rejected(self):
        """Test that negative amounts are rejected."""
        form = DepositForm(
            data={"amount": Decimal("-100.00")},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )

        self.assertFalse(form.is_valid())


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        agencia = 1
        conta = 1001
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=100,
            balance_after_transaction=1100,
            transaction_type=DEPOSIT
        )
        self.assertEqual(transaction.account, self.account)
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(str(transaction), f'{self.account.get_account_number()} - Deposit')


class DepositFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        agencia = 1
        conta = 1002
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )

    def test_valid_deposit(self):
        form_data = {
            'amount': 100,
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertTrue(form.is_valid())

    def test_deposit_below_minimum(self):
        form_data = {
            'amount': 5,
        }
        form = DepositForm(data=form_data, account=self.account, initial={'transaction_type': DEPOSIT})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class WithdrawFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        agencia = 1
        conta = 1003
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )

    def test_valid_withdrawal(self):
        form_data = {
            'amount': 100,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertTrue(form.is_valid())

    def test_withdrawal_below_minimum(self):
        form_data = {
            'amount': 5,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())

    def test_withdrawal_above_maximum(self):
        form_data = {
            'amount': 10000,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())

    def test_withdrawal_prevents_negative_balance(self):
        """Test that withdrawals that exceed balance are rejected (enterprise validation)."""
        form_data = {
            'amount': 2000,
        }
        form = WithdrawForm(data=form_data, account=self.account, initial={'transaction_type': WITHDRAWAL})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class TransactionDateRangeFormTest(TestCase):
    def test_valid_date_range(self):
        form_data = {
            'date_from': '2024-01-01',
            'date_to': '2024-01-31'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_date_range(self):
        form_data = {
            'date_from': '2024-01-31',
            'date_to': '2024-01-01'
        }
        form = TransactionDateRangeForm(data=form_data)
        self.assertFalse(form.is_valid())


class CalculateInterestTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_interest_calculation_task(self):
        from datetime import date
        from dateutil.relativedelta import relativedelta

        agencia = 1
        conta = 1004
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000,
            initial_deposit_date=date.today(),
            interest_start_date=date.today() + relativedelta(months=1)
        )

        initial_balance = account.balance
        calculate_interest()

        account.refresh_from_db()
        self.assertGreaterEqual(account.balance, initial_balance)
