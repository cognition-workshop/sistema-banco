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
        
        self.user_with_account = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user_with_account,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        self.user_without_account = User.objects.create_user(
            email='noaccount@example.com',
            password='testpass123'
        )
    
    def test_get_balance_authenticated_with_account(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get('/accounts/api/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['balance']), Decimal('1000.00'))
        self.assertEqual(response.data['account_type_name'], 'Savings Account')
    
    def test_get_balance_unauthenticated(self):
        response = self.client.get('/accounts/api/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_balance_user_without_account(self):
        self.client.force_authenticate(user=self.user_without_account)
        response = self.client.get('/accounts/api/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
    
    def test_users_can_only_access_own_account(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get('/accounts/api/balance/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], self.account.account_no)
