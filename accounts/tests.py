from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import UserBankAccount, BankAccountType, UserAddress

User = get_user_model()


class UserRegistrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )

    def test_user_registration_creates_account(self):
        response = self.client.post(
            reverse('accounts:user_registration'),
            {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'newuser@example.com',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'account_type': self.account_type.id,
                'gender': 'M',
                'birth_date': '1990-01-01',
                'street_address': '123 Test St',
                'city': 'Test City',
                'postal_code': '12345',
                'country': 'Test Country'
            }
        )
        
        user = User.objects.filter(email='newuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertTrue(hasattr(user, 'account'))

    def test_authenticated_user_redirect(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        UserBankAccount.objects.create(
            user=user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('0')
        )
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('accounts:user_registration'))
        self.assertEqual(response.status_code, 302)


class UserLoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_user_can_login(self):
        response = self.client.post(
            reverse('accounts:user_login'),
            {'username': 'test@example.com', 'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(
            reverse('accounts:user_login'),
            {'username': 'test@example.com', 'password': 'wrongpassword'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')


class UserBankAccountTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_account_creation(self):
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        self.assertEqual(account.user, self.user)
        self.assertEqual(account.balance, Decimal('1000.00'))

    def test_user_balance_property(self):
        UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1500.00')
        )
        self.assertEqual(self.user.balance, Decimal('1500.00'))


class BankAccountTypeTestCase(TestCase):
    def test_interest_calculation(self):
        account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('12.0'),
            interest_calculation_per_year=12
        )
        
        interest = account_type.calculate_interest(Decimal('1000.00'))
        self.assertEqual(interest, Decimal('10.00'))
