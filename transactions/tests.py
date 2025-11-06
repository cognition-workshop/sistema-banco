from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import DepositForm, WithdrawForm

User = get_user_model()


class TestTransactionModel(TestCase):
    """Testes para modelo Transaction"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.account_type = BankAccountType.objects.create(
            name="Conta Corrente",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("2.50"),
            interest_calculation_per_year=12,
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_transaction_creation(self):
        """Testa criação de transação"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal("100.00"),
            balance_after_transaction=Decimal("1100.00"),
            transaction_type=DEPOSIT,
        )
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.transaction_type, DEPOSIT)


class TestTransactionViews(TestCase):
    """Testes para views de transações"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="demo@example.com", password="testpass123"
        )
        self.account_type = BankAccountType.objects.create(
            name="Conta Corrente",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("2.50"),
            interest_calculation_per_year=12,
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000.00"),
        )

    def test_deposit_view_get(self):
        """Testa acesso à página de depósito"""
        response = self.client.get(reverse("transactions:deposit_money"))
        self.assertEqual(response.status_code, 200)

    def test_deposit_valid_amount(self):
        """Testa depósito com valor válido"""
        initial_balance = self.account.balance
        self.client.post(
            reverse("transactions:deposit_money"),
            {"amount": "100.00", "transaction_type": DEPOSIT},
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal("100.00"))

    def test_withdraw_view_get(self):
        """Testa acesso à página de saque"""
        response = self.client.get(reverse("transactions:withdraw_money"))
        self.assertEqual(response.status_code, 200)

    def test_withdraw_valid_amount(self):
        """Testa saque com valor válido"""
        initial_balance = self.account.balance
        self.client.post(
            reverse("transactions:withdraw_money"),
            {"amount": "100.00", "transaction_type": WITHDRAWAL},
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal("100.00"))

    def test_withdraw_insufficient_balance(self):
        """Testa que saque com saldo insuficiente é bloqueado"""
        form = WithdrawForm(
            data={"amount": "2000.00"},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Saldo insuficiente", str(form.errors))


class TestDepositForm(TestCase):
    """Testes para formulário de depósito"""

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="test")
        self.account_type = BankAccountType.objects.create(
            name="Test",
            maximum_withdrawal_amount=Decimal("5000"),
            annual_interest_rate=Decimal("2.5"),
            interest_calculation_per_year=12,
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000"),
        )

    def test_deposit_minimum_amount(self):
        """Testa depósito com valor mínimo"""
        form = DepositForm(
            data={"amount": "5.00"},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )
        self.assertFalse(form.is_valid())

    def test_deposit_valid_amount(self):
        """Testa depósito com valor válido"""
        form = DepositForm(
            data={"amount": "100.00"},
            initial={"transaction_type": DEPOSIT},
            account=self.account,
        )
        self.assertTrue(form.is_valid())


class TestWithdrawForm(TestCase):
    """Testes para formulário de saque"""

    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="test")
        self.account_type = BankAccountType.objects.create(
            name="Test",
            maximum_withdrawal_amount=Decimal("5000"),
            annual_interest_rate=Decimal("2.5"),
            interest_calculation_per_year=12,
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1234567890,
            gender="M",
            balance=Decimal("1000"),
        )

    def test_withdraw_exceeds_balance(self):
        """Testa que saque maior que saldo é rejeitado"""
        form = WithdrawForm(
            data={"amount": "1500.00"},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_withdraw_exceeds_maximum(self):
        """Testa que saque maior que limite é rejeitado"""
        self.account.balance = Decimal("10000")
        self.account.save()

        form = WithdrawForm(
            data={"amount": "6000.00"},
            initial={"transaction_type": WITHDRAWAL},
            account=self.account,
        )
        self.assertFalse(form.is_valid())


class TestTransactionValidators(TestCase):
    """Testes para validadores de transações"""

    def test_validate_minimum_deposit(self):
        """Testa validador de depósito mínimo"""
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from transactions.validators import validate_minimum_deposit

        validate_minimum_deposit(Decimal("100.00"))

        with self.assertRaises(ValidationError):
            validate_minimum_deposit(Decimal("5.00"))

    def test_validate_minimum_withdrawal(self):
        """Testa validador de saque mínimo"""
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from transactions.validators import validate_minimum_withdrawal

        validate_minimum_withdrawal(Decimal("100.00"))

        with self.assertRaises(ValidationError):
            validate_minimum_withdrawal(Decimal("5.00"))
