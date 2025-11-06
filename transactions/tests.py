from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date

from .models import Transaction
from .serializers import TransactionSerializer
from .constants import DEPOSIT, WITHDRAWAL, INTEREST
from accounts.models import UserBankAccount, BankAccountType
from accounts.constants import MALE

User = get_user_model()


class TransactionSerializerTest(TestCase):
    """Test TransactionSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
    
    def test_serialization_with_computed_fields(self):
        """Test serializing a Transaction with computed fields"""
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        
        serializer = TransactionSerializer(transaction)
        data = serializer.data
        
        self.assertEqual(Decimal(data['amount']), Decimal('100.00'))
        self.assertEqual(Decimal(data['balance_after_transaction']), Decimal('1100.00'))
        self.assertEqual(data['transaction_type'], DEPOSIT)
        self.assertEqual(data['transaction_type_display'], 'Deposit')
        self.assertEqual(data['account_no'], 1000000001)
    
    def test_all_fields_read_only(self):
        """Test that all fields are read-only"""
        data = {
            'amount': '200.00',
            'balance_after_transaction': '1200.00',
            'transaction_type': WITHDRAWAL
        }
        
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class TransactionViewSetTest(APITestCase):
    """Test TransactionViewSet API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('2.50'),
            interest_calculation_per_year=12
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='regularpass123'
        )
        self.regular_account = UserBankAccount.objects.create(
            user=self.regular_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender=MALE,
            balance=Decimal('1000.00')
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.other_account = UserBankAccount.objects.create(
            user=self.other_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender=MALE,
            balance=Decimal('2000.00')
        )
        
        self.user_no_account = User.objects.create_user(
            email='noaccount@example.com',
            password='noaccountpass123'
        )
        
        self.transaction1 = Transaction.objects.create(
            account=self.regular_account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('1100.00'),
            transaction_type=DEPOSIT
        )
        self.transaction2 = Transaction.objects.create(
            account=self.regular_account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('1050.00'),
            transaction_type=WITHDRAWAL
        )
        self.transaction3 = Transaction.objects.create(
            account=self.other_account,
            amount=Decimal('200.00'),
            balance_after_transaction=Decimal('2200.00'),
            transaction_type=DEPOSIT
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_staff_can_list_all_transactions(self):
        """Test that staff users can see all transactions"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_regular_user_can_only_list_their_transactions(self):
        """Test that regular users can only see their own transactions"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        for transaction in response.data['results']:
            self.assertEqual(transaction['account_no'], 1000000001)
    
    def test_user_without_account_gets_empty_queryset(self):
        """Test that users without account get empty queryset"""
        self.client.force_authenticate(user=self.user_no_account)
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_retrieve_transaction(self):
        """Test retrieving a specific transaction"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/transactions/{self.transaction1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_no'], 1000000001)
        self.assertEqual(Decimal(response.data['amount']), Decimal('100.00'))
    
    def test_cannot_retrieve_other_user_transaction(self):
        """Test that users cannot retrieve other users' transactions"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/transactions/{self.transaction3.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_not_allowed(self):
        """Test that creating transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'account': self.regular_account.id,
            'amount': '50.00',
            'balance_after_transaction': '1150.00',
            'transaction_type': DEPOSIT
        }
        response = self.client.post('/api/transactions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_update_not_allowed(self):
        """Test that updating transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        data = {'amount': '999.99'}
        response = self.client.patch(f'/api/transactions/{self.transaction1.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_not_allowed(self):
        """Test that deleting transactions is not allowed (read-only)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(f'/api/transactions/{self.transaction1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_ordering_by_timestamp(self):
        """Test ordering transactions by timestamp"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?ordering=-timestamp')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['id'], self.transaction3.id)
    
    def test_ordering_by_amount(self):
        """Test ordering transactions by amount"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?ordering=amount')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(Decimal(results[0]['amount']), Decimal('50.00'))
    
    def test_search_by_account_no(self):
        """Test searching transactions by account number"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/transactions/?search=1000000001')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        for transaction in response.data['results']:
            self.assertEqual(transaction['account_no'], 1000000001)
