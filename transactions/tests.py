from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

User = get_user_model()


class TransactionFilterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            balance_after_transaction=Decimal('100.00'),
            transaction_type=DEPOSIT
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            balance_after_transaction=Decimal('50.00'),
            transaction_type=WITHDRAWAL
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('5.00'),
            balance_after_transaction=Decimal('55.00'),
            transaction_type=INTEREST
        )
        
        self.client = Client()

    def test_filter_by_deposit(self):
        response = self.client.get('/transactions/report/', {'transaction_type': DEPOSIT})
        self.assertEqual(response.status_code, 200)
        transactions = response.context['object_list']
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions[0].transaction_type, DEPOSIT)

    def test_filter_by_withdrawal(self):
        response = self.client.get('/transactions/report/', {'transaction_type': WITHDRAWAL})
        self.assertEqual(response.status_code, 200)
        transactions = response.context['object_list']
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions[0].transaction_type, WITHDRAWAL)

    def test_filter_by_interest(self):
        response = self.client.get('/transactions/report/', {'transaction_type': INTEREST})
        self.assertEqual(response.status_code, 200)
        transactions = response.context['object_list']
        self.assertEqual(transactions.count(), 1)
        self.assertEqual(transactions[0].transaction_type, INTEREST)

    def test_no_filter_shows_all(self):
        response = self.client.get('/transactions/report/')
        self.assertEqual(response.status_code, 200)
        transactions = response.context['object_list']
        self.assertEqual(transactions.count(), 3)
