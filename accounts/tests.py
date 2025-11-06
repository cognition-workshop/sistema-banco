from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import UserBankAccount, BankAccountType

User = get_user_model()


class AccountBalanceAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.account_type = BankAccountType.objects.create(
            name='Savings Account',
            maximum_withdrawal_amount=10000.00,
            annual_interest_rate=5.0,
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
            balance=1500.50
        )
        
        self.user_without_account = User.objects.create_user(
            email='noaccountuser@example.com',
            password='testpass123'
        )
        
        self.url = reverse('accounts:account_balance_api')
    
    def test_authenticated_user_can_access_own_balance(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(float(response.data['balance']), 1500.50)
        self.assertEqual(response.data['account_type_name'], 'Savings Account')
    
    def test_unauthenticated_user_cannot_access_balance(self):
        response = self.client.get(self.url)
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_user_without_account_gets_404(self):
        self.client.force_authenticate(user=self.user_without_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_response_contains_required_fields(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('account_no', response.data)
        self.assertIn('balance', response.data)
        self.assertIn('account_type_name', response.data)
