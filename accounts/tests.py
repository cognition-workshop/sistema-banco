from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from .models import UserBankAccount, BankAccountType


User = get_user_model()


class AccountBalanceAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=Decimal('5000.00'),
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
            balance=Decimal('1000.00')
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
            balance=Decimal('2000.00')
        )
    
    def test_unauthenticated_request_returns_401(self):
        url = f'/accounts/api/balance/{self.account1.account_no}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_user_can_access_own_account(self):
        self.client.force_authenticate(user=self.user1)
        url = f'/accounts/api/balance/{self.account1.account_no}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], self.account1.account_no)
        self.assertEqual(Decimal(response.data['balance']), self.account1.balance)
        self.assertEqual(response.data['account_type_name'], self.account_type.name)
    
    def test_authenticated_user_cannot_access_other_account(self):
        self.client.force_authenticate(user=self.user1)
        url = f'/accounts/api/balance/{self.account2.account_no}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_nonexistent_account_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        url = '/accounts/api/balance/9999999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_response_format_is_correct(self):
        self.client.force_authenticate(user=self.user1)
        url = f'/accounts/api/balance/{self.account1.account_no}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('account_no', response.data)
        self.assertIn('balance', response.data)
        self.assertIn('account_type_name', response.data)
        self.assertEqual(len(response.data), 3)
