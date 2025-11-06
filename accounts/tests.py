from decimal import Decimal
from datetime import date, datetime
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import User, BankAccountType, UserBankAccount, UserAddress
from accounts.forms import UserAddressForm, UserRegistrationForm
from accounts.utils import calcular_digito_verificador
from accounts.serializers import (
    UserSerializer,
    UserBankAccountSerializer,
    BankAccountTypeSerializer,
    UserAddressSerializer
)
from accounts.constants import MALE, FEMALE

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(str(self.user), 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)

    def test_user_balance_with_account(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1500.50
        )
        self.assertEqual(self.user.balance, Decimal('1500.50'))


class BankAccountTypeModelTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_account_type_creation(self):
        self.assertEqual(self.account_type.name, 'Savings Account')
        self.assertEqual(self.account_type.annual_interest_rate, Decimal('5.0'))

    def test_account_type_str(self):
        self.assertEqual(str(self.account_type), 'Savings Account')

    def test_calculate_interest_monthly(self):
        principal = Decimal('1000.00')
        interest = self.account_type.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('5.0')/100) / 12))) - principal, 2)
        self.assertEqual(interest, expected)
        self.assertGreater(interest, 0)

    def test_calculate_interest_quarterly(self):
        account_type = BankAccountType.objects.create(
            name='Current Account',
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=3.0,
            interest_calculation_per_year=4
        )
        principal = Decimal('5000.00')
        interest = account_type.calculate_interest(principal)
        expected = round((principal * (1 + ((Decimal('3.0')/100) / 4))) - principal, 2)
        self.assertEqual(interest, expected)

    def test_calculate_interest_zero_principal(self):
        interest = self.account_type.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0.00'))


class UserBankAccountModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='account@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_account_creation_without_brazilian_format(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=1000.00
        )
        self.assertEqual(str(account), '1000000001')
        self.assertEqual(account.get_formatted_account(), 'Conta 1000000001')

    def test_account_creation_with_brazilian_format(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            agencia='1234',
            conta_digito='5',
            gender=FEMALE,
            birth_date=date(1995, 5, 15),
            balance=2500.00
        )
        self.assertEqual(str(account), 'Ag. 1234 - C/C 1000000001-5')
        self.assertEqual(account.get_formatted_account(), 'Agência 1234 - Conta 1000000001-5')

    def test_get_interest_calculation_months_monthly(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 1, 15)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    def test_get_interest_calculation_months_quarterly(self):
        quarterly_type = BankAccountType.objects.create(
            name='Quarterly',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=4.0,
            interest_calculation_per_year=4
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=quarterly_type,
            account_no=1000000002,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            interest_start_date=date(2024, 3, 1)
        )
        months = account.get_interest_calculation_months()
        self.assertEqual(months, [3, 6, 9, 12])

    def test_account_balance_default(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000003,
            gender=MALE,
            birth_date=date(1990, 1, 1)
        )
        self.assertEqual(account.balance, Decimal('0'))


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='address@example.com',
            password='testpass123'
        )

    def test_address_creation(self):
        address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Test Street',
            city='São Paulo',
            postal_code=12345678,
            country='Brazil'
        )
        self.assertEqual(address.street_address, '123 Test Street')
        self.assertEqual(address.city, 'São Paulo')
        self.assertEqual(str(address), 'address@example.com')


class UserRegistrationFormTest(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )

    def test_valid_registration_form(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_creates_user_and_account(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': FEMALE,
            'birth_date': '1995-05-15'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'jane@example.com')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, FEMALE)
        self.assertEqual(user.account.account_type, self.account_type)
        expected_account_no = user.id + settings.ACCOUNT_NUMBER_START_FROM
        self.assertEqual(user.account.account_no, expected_account_no)

    def test_registration_form_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
            'account_type': self.account_type.id,
            'gender': MALE,
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class UserAddressFormTest(TestCase):
    def test_valid_address_form(self):
        form_data = {
            'street_address': '456 Main St',
            'city': 'Rio de Janeiro',
            'postal_code': 20000000,
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_address_form_missing_required_field(self):
        form_data = {
            'street_address': '456 Main St',
            'city': 'Rio de Janeiro',
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)


class CalcularDigitoVerificadorTest(TestCase):
    def test_calcular_digito_verificador_basic(self):
        digito = calcular_digito_verificador('1234', '123456')
        self.assertIn(digito, '0123456789X')

    def test_calcular_digito_verificador_returns_x_for_high_values(self):
        digito = calcular_digito_verificador('9999', '999999')
        self.assertTrue(isinstance(digito, str))

    def test_calcular_digito_verificador_with_integers(self):
        digito = calcular_digito_verificador(1234, 123456)
        self.assertIn(digito, '0123456789X')

    def test_calcular_digito_verificador_consistency(self):
        digito1 = calcular_digito_verificador('1234', '567890')
        digito2 = calcular_digito_verificador('1234', '567890')
        self.assertEqual(digito1, digito2)


class UserAddressSerializerTest(TestCase):
    """Test UserAddressSerializer"""
    
    def test_serialization(self):
        """Test serializing a UserAddress instance"""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        address = UserAddress.objects.create(
            user=user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )
        
        serializer = UserAddressSerializer(address)
        data = serializer.data
        
        self.assertEqual(data['street_address'], '123 Test St')
        self.assertEqual(data['city'], 'Test City')
        self.assertEqual(data['postal_code'], 12345)
        self.assertEqual(data['country'], 'Test Country')
    
    def test_deserialization(self):
        """Test deserializing address data"""
        data = {
            'street_address': '456 New St',
            'city': 'New City',
            'postal_code': 67890,
            'country': 'New Country'
        }
        
        serializer = UserAddressSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['street_address'], '456 New St')


class BankAccountTypeSerializerTest(TestCase):
    """Test BankAccountTypeSerializer"""
    
    def test_serialization(self):
        """Test serializing a BankAccountType instance"""
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        
        serializer = BankAccountTypeSerializer(account_type)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Savings')
        self.assertEqual(Decimal(data['maximum_withdrawal_amount']), Decimal('5000.00'))
        self.assertEqual(Decimal(data['annual_interest_rate']), Decimal('2.50'))
        self.assertEqual(data['interest_calculation_per_year'], 12)
    
    def test_read_only_id_field(self):
        """Test that id field is read-only"""
        data = {
            'id': 999,
            'name': 'Checking',
            'maximum_withdrawal_amount': '10000.00',
            'annual_interest_rate': '1.50',
            'interest_calculation_per_year': 12
        }
        
        serializer = BankAccountTypeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('id', serializer.validated_data)


class UserBankAccountSerializerTest(TestCase):
    """Test UserBankAccountSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
    
    def test_serialization_with_nested_account_type(self):
        """Test serializing a UserBankAccount with nested account_type"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            birth_date=date(1990, 1, 1),
            balance=Decimal('1000.00')
        )
        
        serializer = UserBankAccountSerializer(account)
        data = serializer.data
        
        self.assertEqual(data['account_no'], 1000000001)
        self.assertEqual(data['gender'], MALE)
        self.assertIn('account_type', data)
        self.assertEqual(data['account_type']['name'], 'Savings')
    
    def test_account_type_id_write_only(self):
        """Test that account_type_id is write-only"""
        data = {
            'account_type_id': self.account_type.id,
            'gender': FEMALE,
            'birth_date': '1995-05-15'
        }
        
        serializer = UserBankAccountSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['account_type'], self.account_type)
    
    def test_read_only_fields(self):
        """Test that certain fields are read-only"""
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            balance=Decimal('500.00')
        )
        
        data = {
            'account_no': 9999999999,
            'balance': '99999.99',
            'gender': FEMALE
        }
        
        serializer = UserBankAccountSerializer(account, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        account.refresh_from_db()
        self.assertEqual(account.account_no, 1000000002)
        self.assertEqual(account.balance, Decimal('500.00'))
        self.assertEqual(account.gender, FEMALE)


class UserSerializerTest(TestCase):
    """Test UserSerializer"""
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
    
    def test_serialization_with_nested_address_and_account(self):
        """Test serializing a User with nested address and account"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        UserAddress.objects.create(
            user=user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )
        UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
        serializer = UserSerializer(user)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertIn('address', data)
        self.assertEqual(data['address']['city'], 'Test City')
        self.assertIn('account', data)
        self.assertEqual(data['account']['account_no'], 1000000001)
        self.assertEqual(Decimal(data['balance']), Decimal('1000.00'))
    
    def test_create_user_with_address(self):
        """Test creating a user with nested address"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'address': {
                'street_address': '456 New St',
                'city': 'New City',
                'postal_code': 67890,
                'country': 'New Country'
            }
        }
        
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
        self.assertTrue(hasattr(user, 'address'))
        self.assertEqual(user.address.city, 'New City')
    
    def test_update_user_with_address(self):
        """Test updating a user with nested address"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        UserAddress.objects.create(
            user=user,
            street_address='Old St',
            city='Old City',
            postal_code=11111,
            country='Old Country'
        )
        
        data = {
            'first_name': 'Updated',
            'address': {
                'street_address': 'New St',
                'city': 'New City',
                'postal_code': 22222,
                'country': 'New Country'
            }
        }
        
        serializer = UserSerializer(user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.first_name, 'Updated')
        user.address.refresh_from_db()
        self.assertEqual(user.address.city, 'New City')


class UserViewSetTest(APITestCase):
    """Test UserViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_list_all_users(self):
        """Test that staff users can see all users"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_regular_user_can_only_list_themselves(self):
        """Test that regular users can only see themselves"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], 'regular@example.com')
    
    def test_staff_can_retrieve_any_user(self):
        """Test that staff can retrieve any user"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(f'/api/users/{self.regular_user.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'regular@example.com')
    
    def test_regular_user_can_only_retrieve_themselves(self):
        """Test that regular users can only retrieve themselves"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(f'/api/users/{self.regular_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = self.client.get(f'/api/users/{self.other_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_can_update_themselves(self):
        """Test that users can update their own data"""
        self.client.force_authenticate(user=self.regular_user)
        data = {'first_name': 'Updated'}
        response = self.client.patch(f'/api/users/{self.regular_user.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')


class UserBankAccountViewSetTest(APITestCase):
    """Test UserBankAccountViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.regular_account = UserBankAccount.objects.create(
            user=self.regular_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        self.other_account = UserBankAccount.objects.create(
            user=self.other_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=FEMALE,
            balance=Decimal('2000.00')
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/bank-accounts/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_list_all_accounts(self):
        """Test that staff users can see all bank accounts"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/bank-accounts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_regular_user_can_only_list_their_account(self):
        """Test that regular users can only see their own account"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/bank-accounts/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['account_no'], 1000000001)


class BankAccountTypeViewSetTest(APITestCase):
    """Test BankAccountTypeViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type1 = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        self.account_type2 = BankAccountType.objects.create(
            name='Checking',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('1.00'),
            interest_calculation_per_year=12
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/account-types/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_authenticated_user_can_list_account_types(self):
        """Test that authenticated users can list all account types"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/account-types/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_authenticated_user_can_retrieve_account_type(self):
        """Test that authenticated users can retrieve account types"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/account-types/{self.account_type1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Savings')
    
    def test_create_not_allowed(self):
        """Test that creating account types is not allowed (read-only)"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Type',
            'maximum_withdrawal_amount': '1000.00',
            'annual_interest_rate': '3.00',
            'interest_calculation_per_year': 12
        }
        response = self.client.post('/api/account-types/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_not_allowed(self):
        """Test that updating account types is not allowed (read-only)"""
        self.client.force_authenticate(user=self.user)
        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/account-types/{self.account_type1.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_not_allowed(self):
        """Test that deleting account types is not allowed (read-only)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/account-types/{self.account_type1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UserAddressViewSetTest(APITestCase):
    """Test UserAddressViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.regular_address = UserAddress.objects.create(
            user=self.regular_user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )
        self.other_address = UserAddress.objects.create(
            user=self.other_user,
            street_address='456 Other St',
            city='Other City',
            postal_code=67890,
            country='Other Country'
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/addresses/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_staff_can_list_all_addresses(self):
        """Test that staff users can see all addresses"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/addresses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_regular_user_can_only_list_their_address(self):
        """Test that regular users can only see their own address"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/addresses/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['city'], 'Test City')
