from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import UserBankAccount, BankAccountType


User = get_user_model()


class AccountBalanceAPITestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
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
        
        self.user_no_account = User.objects.create_user(
            email='noaccount@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.url = '/accounts/api/balance/'
    
    def test_authenticated_user_can_get_own_balance(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['balance']), Decimal('1000.00'))
        self.assertEqual(response.data['account_type'], 'Savings')
    
    def test_unauthenticated_user_gets_403(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_without_account_gets_404(self):
        self.client.force_authenticate(user=self.user_no_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['detail'].lower())
    
    def test_different_users_get_their_own_balance(self):
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get(self.url)
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response1.data['balance']), Decimal('1000.00'))
        
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get(self.url)
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['account_no'], 1000000002)
        self.assertEqual(Decimal(response2.data['balance']), Decimal('2000.00'))
        
        self.assertNotEqual(response1.data['account_no'], response2.data['account_no'])
        self.assertNotEqual(response1.data['balance'], response2.data['balance'])
