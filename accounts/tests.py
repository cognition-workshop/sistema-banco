from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import BankAccountType, UserBankAccount, UserAddress
from .forms import UserRegistrationForm, UserAddressForm
from .utils import validate_brazilian_account

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)
    
    def test_user_balance_with_account(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        agencia = 1
        conta = 3001
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            cpf='123.456.789-09',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )
        self.assertEqual(self.user.balance, 1000)


class BankAccountTypeModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
    
    def test_account_type_creation(self):
        self.assertEqual(self.account_type.name, 'Savings')
        self.assertEqual(str(self.account_type), 'Savings')
    
    def test_interest_calculation(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal)
        self.assertGreater(interest, 0)
        self.assertIsInstance(interest, Decimal)


class UserBankAccountModelTest(TestCase):
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
        conta = 3002
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='111.444.777-35',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )
    
    def test_account_creation(self):
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.account.balance, 1000)
        self.assertEqual(str(self.account), self.account.get_account_number())
    
    def test_get_interest_calculation_months(self):
        from datetime import date
        self.account.interest_start_date = date(2024, 1, 15)
        months = self.account.get_interest_calculation_months()
        self.assertIsInstance(months, list)
        self.assertGreater(len(months), 0)


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )
    
    def test_address_creation(self):
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.city, 'Test City')
        self.assertEqual(str(self.address), 'test@example.com')


class UserRegistrationFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
    
    def test_valid_form(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01',
            'cpf': '123.456.789-09'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_creates_account(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01',
            'cpf': '111.444.777-35'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, 'M')


class UserAddressFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'street_address': '123 Main St',
            'city': 'Test City',
            'postal_code': 12345,
            'country': 'Test Country'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())
