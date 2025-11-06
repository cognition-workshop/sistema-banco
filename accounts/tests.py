from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserBankAccount, BankAccountType
from decimal import Decimal

User = get_user_model()


class AccountBalanceAPITestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user_with_account = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user_with_account,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1500.50')
        )
        
        self.user_without_account = User.objects.create_user(
            email='noaccountuser@example.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.url = reverse('accounts:api_account_balance')
    
    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_authenticated_user_can_view_own_balance(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['balance']), Decimal('1500.50'))
        self.assertEqual(response.data['account_type_name'], 'Savings')
        self.assertEqual(response.data['user_email'], 'testuser@example.com')
    
    def test_user_without_account_gets_404(self):
        self.client.force_authenticate(user=self.user_without_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
