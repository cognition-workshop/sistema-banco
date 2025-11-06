from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import BankAccountType, UserBankAccount
from .utils import validate_brazilian_account

User = get_user_model()


class AccountAPITest(APITestCase):
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
        agencia = 1
        conta = 4001
        agencia_digito, conta_digito = validate_brazilian_account(agencia, conta)
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            cpf='111.444.777-35',
            agencia=str(agencia).zfill(4),
            agencia_digito=str(agencia_digito),
            conta=str(conta).zfill(8),
            conta_digito=str(conta_digito),
            gender='M',
            balance=1000
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_users_list(self):
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_current_user(self):
        response = self.client.get('/api/accounts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_get_bank_accounts(self):
        response = self.client.get('/api/accounts/bank-accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
