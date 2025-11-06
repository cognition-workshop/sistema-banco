import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserRegistrationForm, UserAddressForm

User = get_user_model()


@pytest.mark.django_db
class AccountTestCase(TestCase):
    """Testes para o sistema de contas."""

    def setUp(self):
        """Configuração inicial para cada teste."""
        self.client = Client()

        self.account_type = BankAccountType.objects.create(
            name="Conta Poupança",
            maximum_withdrawal_amount=Decimal("3000.00"),
            annual_interest_rate=Decimal("5.0"),
            interest_calculation_per_year=12,
        )

    def test_user_registration_success(self):
        """Teste de registro de usuário bem-sucedido."""
        user_data = {
            "first_name": "João",
            "last_name": "Silva",
            "email": "joao@example.com",
            "password1": "senhaforte123",
            "password2": "senhaforte123",
            "account_type": self.account_type.id,
            "gender": "M",
            "birth_date": "1990-01-01",
        }

        address_data = {
            "street_address": "Rua Teste, 123",
            "city": "São Paulo",
            "postal_code": "01234-567",
            "country": "Brasil",
        }

        data = {**user_data, **address_data}

        response = self.client.post(reverse("accounts:user_registration"), data)

        self.assertTrue(User.objects.filter(email="joao@example.com").exists())
        user = User.objects.get(email="joao@example.com")

        self.assertTrue(hasattr(user, "account"))
        self.assertEqual(user.account.account_type, self.account_type)

        self.assertTrue(hasattr(user, "address"))

    def test_duplicate_email(self):
        """Teste de email duplicado."""
        User.objects.create_user(email="test@example.com", password="pass123")

        form_data = {
            "email": "test@example.com",
            "password1": "senhaforte123",
            "password2": "senhaforte123",
        }

        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_account_balance_property(self):
        """Teste da propriedade balance do usuário."""
        user = User.objects.create_user(email="balance@example.com", password="pass123")

        account = UserBankAccount.objects.create(
            user=user, account_type=self.account_type, account_no=1000000002, gender="M", balance=Decimal("1500.00")
        )

        self.assertEqual(user.balance, Decimal("1500.00"))


@pytest.mark.django_db
class AccountFormTestCase(TestCase):
    """Testes para formulários de conta."""

    def setUp(self):
        """Configuração inicial."""
        self.account_type = BankAccountType.objects.create(
            name="Conta Teste",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("3.0"),
            interest_calculation_per_year=12,
        )

    def test_postal_code_validation(self):
        """Teste de validação de CEP."""
        valid_cep = "12345-678"
        invalid_cep = "123"

        form_valid = UserAddressForm(
            data={"street_address": "Rua A", "city": "São Paulo", "postal_code": valid_cep, "country": "Brasil"}
        )

        form_invalid = UserAddressForm(
            data={"street_address": "Rua B", "city": "Rio de Janeiro", "postal_code": invalid_cep, "country": "Brasil"}
        )

        self.assertTrue(form_valid.is_valid())
        self.assertFalse(form_invalid.is_valid())
