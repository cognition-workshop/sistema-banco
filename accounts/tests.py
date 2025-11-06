from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from accounts.validators import validate_cpf, validate_account_number
from django.core.exceptions import ValidationError

User = get_user_model()


class TestUserModel(TestCase):
    """Testes para o modelo User"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_user_creation(self):
        """Testa criação de usuário"""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))

    def test_user_string_representation(self):
        """Testa representação string do usuário"""
        self.assertEqual(str(self.user), "test@example.com")

    def test_user_balance_without_account(self):
        """Testa que usuário sem conta tem saldo 0"""
        self.assertEqual(self.user.balance, 0)


class TestBankAccountModel(TestCase):
    """Testes para contas bancárias"""

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

    def test_account_creation(self):
        """Testa criação de conta bancária"""
        self.assertEqual(self.account.account_no, 1234567890)
        self.assertEqual(self.account.balance, Decimal("1000.00"))

    def test_account_type_interest_calculation(self):
        """Testa cálculo de juros"""
        interest = self.account_type.calculate_interest(Decimal("1000.00"))
        self.assertGreater(interest, 0)
        self.assertIsInstance(interest, Decimal)

    def test_account_number_generation(self):
        """Testa que número de conta está no formato brasileiro"""
        self.assertGreaterEqual(self.account.account_no, 1000000000)
        self.assertLessEqual(self.account.account_no, 9999999999)


class TestUserViews(TestCase):
    """Testes para views de usuários"""

    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name="Conta Corrente",
            maximum_withdrawal_amount=Decimal("5000.00"),
            annual_interest_rate=Decimal("2.50"),
            interest_calculation_per_year=12,
        )

    def test_registration_view_get(self):
        """Testa acesso à página de registro"""
        response = self.client.get(reverse("accounts:user_registration"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email")

    def test_registration_view_post_valid(self):
        """Testa registro com dados válidos"""
        data = {
            "email": "newuser@example.com",
            "password1": "testpass123!@#",
            "password2": "testpass123!@#",
            "first_name": "New",
            "last_name": "User",
            "account_type": self.account_type.id,
            "gender": "M",
            "birth_date": "1990-01-01",
            "street_address": "123 Test St",
            "city": "São Paulo",
            "postal_code": "01000000",
            "country": "Brasil",
        }
        self.client.post(reverse("accounts:user_registration"), data)
        self.assertEqual(User.objects.count(), 1)
        created_user = User.objects.first()
        self.assertEqual(created_user.email, "newuser@example.com")
        self.assertTrue(hasattr(created_user, "account"))

    def test_login_view(self):
        """Testa login de usuário"""
        User.objects.create_user(email="test@example.com", password="testpass123")
        response = self.client.post(
            reverse("accounts:user_login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)


class TestValidators(TestCase):
    """Testes para validadores customizados"""

    def test_valid_cpf(self):
        """Testa CPF válido"""
        cpf = validate_cpf("11144477735")
        self.assertEqual(cpf, "11144477735")

    def test_valid_cpf_with_formatting(self):
        """Testa CPF válido com formatação"""
        cpf = validate_cpf("111.444.777-35")
        self.assertEqual(cpf, "11144477735")

    def test_invalid_cpf_length(self):
        """Testa CPF com tamanho inválido"""
        with self.assertRaises(ValidationError):
            validate_cpf("123")

    def test_invalid_cpf_repeated_digits(self):
        """Testa CPF com dígitos repetidos"""
        with self.assertRaises(ValidationError):
            validate_cpf("11111111111")

    def test_invalid_cpf_checksum(self):
        """Testa CPF com dígitos verificadores inválidos"""
        with self.assertRaises(ValidationError):
            validate_cpf("11144477736")

    def test_account_number_validation(self):
        """Testa validação de número de conta"""
        validate_account_number(1234567890)

        with self.assertRaises(ValidationError):
            validate_account_number(123)

    def test_positive_amount_validation(self):
        """Testa validação de valores positivos"""
        from decimal import Decimal
        from accounts.validators import validate_positive_amount

        validate_positive_amount(Decimal("100.00"))

        with self.assertRaises(ValidationError):
            validate_positive_amount(Decimal("0"))

        with self.assertRaises(ValidationError):
            validate_positive_amount(Decimal("-10"))
