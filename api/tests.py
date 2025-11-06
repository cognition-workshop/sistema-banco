from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import UserBankAccount, BankAccountType

User = get_user_model()


class AccountBalanceAPITestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.account1 = UserBankAccount.objects.create(
            user=self.user1,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1500.50')
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )
        self.account2 = UserBankAccount.objects.create(
            user=self.user2,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('2500.75')
        )
        
        self.user_no_account = User.objects.create_user(
            email='noaccount@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()

    def get_jwt_token(self, email, password):
        response = self.client.post('/api/token/', {
            'email': email,
            'password': password
        })
        return response.data['access']

    def test_get_balance_authenticated_own_account(self):
        token = self.get_jwt_token('user1@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/v1/accounts/{self.account1.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['accountId'], str(self.account1.account_no))
        self.assertEqual(Decimal(response.data['balance']), Decimal('1500.50'))
        self.assertEqual(response.data['currency'], 'BRL')

    def test_get_balance_unauthenticated(self):
        response = self.client.get(f'/api/v1/accounts/{self.account1.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_balance_another_users_account(self):
        token = self.get_jwt_token('user1@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/v1/accounts/{self.account2.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('permission', response.data['detail'].lower())

    def test_get_balance_nonexistent_account(self):
        token = self.get_jwt_token('user1@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/v1/accounts/9999999999/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_jwt_token_obtain(self):
        response = self.client.post('/api/token/', {
            'email': 'user1@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_token_obtain_invalid_credentials(self):
        response = self.client.post('/api/token/', {
            'email': 'user1@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_refresh(self):
        response = self.client.post('/api/token/', {
            'email': 'user1@example.com',
            'password': 'testpass123'
        })
        refresh_token = response.data['refresh']
        
        response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_balance_format_decimal_precision(self):
        token = self.get_jwt_token('user1@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/v1/accounts/{self.account1.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        balance_str = str(response.data['balance'])
        self.assertEqual(len(balance_str.split('.')[-1]), 2)

    def test_response_contains_all_required_fields(self):
        token = self.get_jwt_token('user1@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/v1/accounts/{self.account1.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('accountId', response.data)
        self.assertIn('balance', response.data)
        self.assertIn('currency', response.data)
        self.assertEqual(len(response.data), 3)

    def test_user_without_account_cannot_access_any_account(self):
        token = self.get_jwt_token('noaccount@example.com', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/v1/accounts/{self.account1.account_no}/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
