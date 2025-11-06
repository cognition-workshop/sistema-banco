from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import BankAccountType, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


class TransactionBalanceTests(TestCase):

    def setUp(self):
        User = get_user_model()
        
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.00'),
            interest_calculation_per_year=12
        )
        
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='testpass123'
        )
        self.demo_account = UserBankAccount.objects.create(
            user=self.demo_user,
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

    def test_deposit_updates_balance_correctly(self):
        initial_balance = self.demo_account.balance
        deposit_amount = Decimal('200.00')
        
        response = self.client.post('/transactions/deposit/', {
            'amount': deposit_amount,
            'transaction_type': DEPOSIT
        })
        
        self.demo_account.refresh_from_db()
        self.assertEqual(self.demo_account.balance, initial_balance + deposit_amount)
        
        transaction = Transaction.objects.filter(
            account=self.demo_account,
            transaction_type=DEPOSIT
        ).latest('timestamp')
        self.assertEqual(transaction.amount, deposit_amount)
        self.assertEqual(transaction.balance_after_transaction, initial_balance + deposit_amount)

    def test_withdrawal_updates_balance_correctly(self):
        initial_balance = self.demo_account.balance
        withdrawal_amount = Decimal('100.00')
        
        response = self.client.post('/transactions/withdraw/', {
            'amount': withdrawal_amount,
            'transaction_type': WITHDRAWAL
        })
        
        self.demo_account.refresh_from_db()
        self.assertEqual(self.demo_account.balance, initial_balance - withdrawal_amount)
        
        transaction = Transaction.objects.filter(
            account=self.demo_account,
            transaction_type=WITHDRAWAL
        ).latest('timestamp')
        self.assertEqual(transaction.amount, withdrawal_amount)
        self.assertEqual(transaction.balance_after_transaction, initial_balance - withdrawal_amount)

    def test_withdrawal_prevents_overdraft(self):
        initial_balance = self.demo_account.balance
        overdraft_amount = initial_balance + Decimal('100.00')
        
        response = self.client.post('/transactions/withdraw/', {
            'amount': overdraft_amount,
            'transaction_type': WITHDRAWAL
        })
        
        self.demo_account.refresh_from_db()
        self.assertEqual(self.demo_account.balance, initial_balance)
        
        transaction_count = Transaction.objects.filter(
            account=self.demo_account,
            transaction_type=WITHDRAWAL
        ).count()
        self.assertEqual(transaction_count, 0)

    def test_transfer_updates_both_accounts_correctly(self):
        sender_initial = self.demo_account.balance
        recipient_initial = self.recipient_account.balance
        transfer_amount = Decimal('150.00')
        
        response = self.client.post('/transactions/transfer/', {
            'recipient_account_no': self.recipient_account.account_no,
            'amount': transfer_amount
        })
        
        self.demo_account.refresh_from_db()
        self.recipient_account.refresh_from_db()
        
        self.assertEqual(self.demo_account.balance, sender_initial - transfer_amount)
        self.assertEqual(self.recipient_account.balance, recipient_initial + transfer_amount)
        
        sender_transaction = Transaction.objects.filter(
            account=self.demo_account,
            transaction_type=WITHDRAWAL,
            amount=transfer_amount
        ).latest('timestamp')
        self.assertEqual(sender_transaction.balance_after_transaction, sender_initial - transfer_amount)
        
        recipient_transaction = Transaction.objects.filter(
            account=self.recipient_account,
            transaction_type=DEPOSIT,
            amount=transfer_amount
        ).latest('timestamp')
        self.assertEqual(recipient_transaction.balance_after_transaction, recipient_initial + transfer_amount)

    def test_transfer_prevents_overdraft(self):
        sender_initial = self.demo_account.balance
        recipient_initial = self.recipient_account.balance
        overdraft_amount = sender_initial + Decimal('100.00')
        
        response = self.client.post('/transactions/transfer/', {
            'recipient_account_no': self.recipient_account.account_no,
            'amount': overdraft_amount
        })
        
        self.demo_account.refresh_from_db()
        self.recipient_account.refresh_from_db()
        
        self.assertEqual(self.demo_account.balance, sender_initial)
        self.assertEqual(self.recipient_account.balance, recipient_initial)

    def test_transfer_rejects_nonexistent_recipient(self):
        sender_initial = self.demo_account.balance
        
        response = self.client.post('/transactions/transfer/', {
            'recipient_account_no': 9999999999,
            'amount': Decimal('50.00')
        })
        
        self.demo_account.refresh_from_db()
        self.assertEqual(self.demo_account.balance, sender_initial)

    def test_transfer_rejects_self_transfer(self):
        sender_initial = self.demo_account.balance
        
        response = self.client.post('/transactions/transfer/', {
            'recipient_account_no': self.demo_account.account_no,
            'amount': Decimal('50.00')
        })
        
        self.demo_account.refresh_from_db()
        self.assertEqual(self.demo_account.balance, sender_initial)
