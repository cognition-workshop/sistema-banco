from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, TRANSFER
from transactions.forms import TransferForm, WithdrawForm

User = get_user_model()


class TransferFormTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
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
            account_no=1001,
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
            account_no=1002,
            gender='F',
            balance=Decimal('500.00')
        )

    def test_valid_transfer(self):
        form = TransferForm(
            data={
                'amount': Decimal('100.00'),
                'recipient_account_number': 1002
            },
            initial={'transaction_type': TRANSFER},
            account=self.sender_account
        )
        self.assertTrue(form.is_valid())

    def test_transfer_to_nonexistent_account(self):
        form = TransferForm(
            data={
                'amount': Decimal('100.00'),
                'recipient_account_number': 9999
            },
            initial={'transaction_type': TRANSFER},
            account=self.sender_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('recipient_account_number', form.errors)

    def test_transfer_to_same_account(self):
        form = TransferForm(
            data={
                'amount': Decimal('100.00'),
                'recipient_account_number': 1001
            },
            initial={'transaction_type': TRANSFER},
            account=self.sender_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('recipient_account_number', form.errors)

    def test_transfer_insufficient_balance(self):
        form = TransferForm(
            data={
                'amount': Decimal('2000.00'),
                'recipient_account_number': 1002
            },
            initial={'transaction_type': TRANSFER},
            account=self.sender_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_transfer_negative_amount(self):
        form = TransferForm(
            data={
                'amount': Decimal('-100.00'),
                'recipient_account_number': 1002
            },
            initial={'transaction_type': TRANSFER},
            account=self.sender_account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class WithdrawFormTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1001,
            gender='M',
            balance=Decimal('1000.00')
        )

    def test_withdraw_insufficient_balance(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('2000.00')
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
        self.assertIn('Insufficient balance', str(form.errors['amount']))

    def test_withdraw_valid_amount(self):
        form = WithdrawForm(
            data={
                'amount': Decimal('500.00')
            },
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())
