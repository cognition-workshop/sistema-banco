from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import TRANSFER
from django.urls import reverse

User = get_user_model()


class TransferMoneyTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('10000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.sender_user = User.objects.create_user(
            email='sender@example.com',
            password='testpass123'
        )
        self.sender_account = UserBankAccount.objects.create(
            user=self.sender_user,
            account_type=self.account_type,
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        self.recipient_user = User.objects.create_user(
            email='recipient@example.com',
            password='testpass123'
        )
        self.recipient_account = UserBankAccount.objects.create(
            user=self.recipient_user,
            account_type=self.account_type,
            account_no=1000000002,
            gender='F',
            balance=Decimal('500.00')
        )
        
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.demo_account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            balance=Decimal('2000.00')
        )

    def test_successful_transfer(self):
        url = reverse('transactions:transfer_money')
        data = {
            'recipient_account_no': self.recipient_account.account_no,
            'amount': '100.00',
            'transaction_type': TRANSFER
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 302)
        
        self.demo_account.refresh_from_db()
        self.recipient_account.refresh_from_db()
        
        self.assertEqual(self.demo_account.balance, Decimal('1900.00'))
        self.assertEqual(self.recipient_account.balance, Decimal('600.00'))
        
        sender_transactions = Transaction.objects.filter(
            account=self.demo_account,
            transaction_type=TRANSFER,
            amount=Decimal('100.00')
        )
        self.assertEqual(sender_transactions.count(), 1)
        
        recipient_transactions = Transaction.objects.filter(
            account=self.recipient_account,
            transaction_type=TRANSFER,
            amount=Decimal('100.00')
        )
        self.assertEqual(recipient_transactions.count(), 1)

    def test_transfer_insufficient_balance(self):
        url = reverse('transactions:transfer_money')
        data = {
            'recipient_account_no': self.recipient_account.account_no,
            'amount': '5000.00',
            'transaction_type': TRANSFER
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', 'Insufficient balance. Your current balance is 2000.00 $')

    def test_transfer_to_nonexistent_account(self):
        url = reverse('transactions:transfer_money')
        data = {
            'recipient_account_no': 9999999999,
            'amount': '100.00',
            'transaction_type': TRANSFER
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'recipient_account_no', 'Account number 9999999999 does not exist')

    def test_transfer_to_self(self):
        url = reverse('transactions:transfer_money')
        data = {
            'recipient_account_no': self.demo_account.account_no,
            'amount': '100.00',
            'transaction_type': TRANSFER
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'recipient_account_no', 'Cannot transfer money to your own account')

    def test_transfer_below_minimum_amount(self):
        url = reverse('transactions:transfer_money')
        data = {
            'recipient_account_no': self.recipient_account.account_no,
            'amount': '5.00',
            'transaction_type': TRANSFER
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'amount', 'You can transfer at least 10 $')
