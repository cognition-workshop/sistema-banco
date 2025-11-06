from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserBankAccount, BankAccountType


User = get_user_model()


class AccountBalanceAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
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
            balance=1500.00
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
            balance=2500.00
        )
    
    def test_authenticated_user_can_access_own_account(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/accounts/api/balance/{self.account1.account_no}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], self.account1.account_no)
        self.assertEqual(float(response.data['balance']), 1500.00)
        self.assertEqual(response.data['account_type_name'], 'Savings')
    
    def test_authenticated_user_cannot_access_other_account(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/accounts/api/balance/{self.account2.account_no}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('permission', response.data['detail'].lower())
    
    def test_unauthenticated_user_cannot_access_account(self):
        response = self.client.get(f'/accounts/api/balance/{self.account1.account_no}/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_nonexistent_account_returns_404(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/accounts/api/balance/9999999999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['detail'].lower())
