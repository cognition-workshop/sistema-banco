from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import (
    User,
    BankAccountType,
    UserBankAccount,
    UserAddress
)
from accounts.forms import UserRegistrationForm, UserAddressForm
from accounts.constants import GENDER_CHOICE


class TestUserModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_user_email_is_username(self):
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_user_balance_with_account(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.50')
        )
        self.assertEqual(self.user.balance, Decimal('1000.50'))
    
    def test_user_balance_without_account(self):
        self.assertEqual(self.user.balance, 0)
    
    def test_email_uniqueness(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                password='testpass456'
            )


class TestBankAccountTypeModel(TestCase):
    
    def setUp(self):
        self.savings_account = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        self.current_account = BankAccountType.objects.create(
            name='Current Account',
            maximum_withdrawal_amount=10000,
            annual_interest_rate=3.5,
            interest_calculation_per_year=4
        )
    
    def test_account_type_creation(self):
        self.assertEqual(self.savings_account.name, 'Savings Account')
        self.assertEqual(self.savings_account.maximum_withdrawal_amount, 5000)
        self.assertEqual(self.savings_account.annual_interest_rate, 5)
        self.assertEqual(self.savings_account.interest_calculation_per_year, 12)
    
    def test_account_type_string_representation(self):
        self.assertEqual(str(self.savings_account), 'Savings Account')
    
    def test_calculate_interest_with_5_percent_monthly(self):
        principal = Decimal('1000.00')
        interest = self.savings_account.calculate_interest(principal)
        expected = Decimal('4.17')
        self.assertEqual(interest, expected)
    
    def test_calculate_interest_with_3_5_percent_quarterly(self):
        principal = Decimal('1000.00')
        interest = self.current_account.calculate_interest(principal)
        expected = Decimal('8.75')
        self.assertEqual(interest, expected)
    
    def test_calculate_interest_with_zero_principal(self):
        interest = self.savings_account.calculate_interest(Decimal('0'))
        self.assertEqual(interest, Decimal('0'))
    
    def test_calculate_interest_rounding(self):
        principal = Decimal('333.33')
        interest = self.savings_account.calculate_interest(principal)
        self.assertEqual(interest, round(interest, 2))


class TestUserBankAccountModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='account@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=6,
            interest_calculation_per_year=4
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            birth_date=date(1990, 1, 1),
            balance=Decimal('500.00'),
            interest_start_date=date(2024, 3, 1)
        )
    
    def test_account_creation(self):
        self.assertEqual(self.account.account_no, 1000000001)
        self.assertEqual(self.account.gender, 'M')
        self.assertEqual(self.account.balance, Decimal('500.00'))
    
    def test_account_string_representation(self):
        self.assertEqual(str(self.account), '1000000001')
    
    def test_account_user_relationship(self):
        self.assertEqual(self.account.user, self.user)
        self.assertEqual(self.user.account, self.account)
    
    def test_get_interest_calculation_months_quarterly(self):
        months = self.account.get_interest_calculation_months()
        expected = [3, 6, 9, 12]
        self.assertEqual(months, expected)
    
    def test_get_interest_calculation_months_monthly(self):
        account_type_monthly = BankAccountType.objects.create(
            name='Monthly Interest',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
            interest_calculation_per_year=12
        )
        account = UserBankAccount.objects.create(
            user=User.objects.create_user(email='monthly@example.com', password='pass'),
            account_type=account_type_monthly,
            account_no=1000000002,
            gender='F',
            balance=Decimal('1000.00'),
            interest_start_date=date(2024, 1, 1)
        )
        months = account.get_interest_calculation_months()
        expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.assertEqual(months, expected)


class TestUserAddressModel(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='address@example.com',
            password='testpass123'
        )
        self.address = UserAddress.objects.create(
            user=self.user,
            street_address='123 Main St',
            city='São Paulo',
            postal_code=12345678,
            country='Brazil'
        )
    
    def test_address_creation(self):
        self.assertEqual(self.address.street_address, '123 Main St')
        self.assertEqual(self.address.city, 'São Paulo')
        self.assertEqual(self.address.postal_code, 12345678)
        self.assertEqual(self.address.country, 'Brazil')
    
    def test_address_string_representation(self):
        self.assertEqual(str(self.address), 'address@example.com')
    
    def test_address_user_relationship(self):
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.user.address, self.address)


class TestUserRegistrationForm(TestCase):
    
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5,
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
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_creates_user_and_account(self):
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'account_type': self.account_type.id,
            'gender': 'F',
            'birth_date': '1995-05-15'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertEqual(user.email, 'jane@example.com')
        self.assertEqual(user.first_name, 'Jane')
        self.assertTrue(user.check_password('SecurePass123!'))
        
        self.assertTrue(hasattr(user, 'account'))
        self.assertEqual(user.account.gender, 'F')
        self.assertEqual(user.account.account_type, self.account_type)
        self.assertEqual(
            user.account.account_no,
            user.id + settings.ACCOUNT_NUMBER_START_FROM
        )
    
    def test_form_password_mismatch(self):
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
            'account_type': self.account_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestUserAddressForm(TestCase):
    
    def test_valid_address_form(self):
        form_data = {
            'street_address': '456 Oak Avenue',
            'city': 'Rio de Janeiro',
            'postal_code': 20040020,
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_missing_required_field(self):
        form_data = {
            'street_address': '456 Oak Avenue',
            'city': 'Rio de Janeiro',
            'country': 'Brazil'
        }
        form = UserAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)


from .serializers import (
    UserSerializer,
    UserBankAccountSerializer,
    BankAccountTypeSerializer,
    UserAddressSerializer
)
from .constants import MALE, FEMALE


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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
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
