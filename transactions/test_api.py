from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from .models import Transaction
from .constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class TransactionAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=5000,
            annual_interest_rate=5.0,
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=1000
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_transactions_list(self):
        Transaction.objects.create(
            account=self.account,
            amount=100,
            balance_after_transaction=1100,
            transaction_type=DEPOSIT
        )
        response = self.client.get('/api/transactions/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_deposit_via_api(self):
        response = self.client.post('/api/transactions/transactions/deposit/', {
            'amount': 100
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1100)
    
    def test_withdraw_via_api(self):
        response = self.client.post('/api/transactions/transactions/withdraw/', {
            'amount': 100
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 900)
    
    def test_deposit_below_minimum(self):
        response = self.client.post('/api/transactions/transactions/deposit/', {
            'amount': 5
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
