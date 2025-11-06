from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from accounts.models import User, UserBankAccount, BankAccountType


class AccountBalanceAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('api_account_balance')
        
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
            balance=Decimal('1500.75')
        )
        
        self.user_without_account = User.objects.create_user(
            email='noaccount@example.com',
            password='testpass123'
        )

    def test_authenticated_user_can_access_balance(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['balance']), Decimal('1500.75'))

    def test_unauthenticated_user_receives_403(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_account_receives_404(self):
        self.client.force_authenticate(user=self.user_without_account)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_format(self):
        self.client.force_authenticate(user=self.user_with_account)
        response = self.client.get(self.url)
        
        self.assertIn('account_no', response.data)
        self.assertIn('balance', response.data)
