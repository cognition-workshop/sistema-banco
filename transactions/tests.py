from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction, AuditLog
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


User = get_user_model()


class AuditLogTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=Decimal('10000.00'),
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
    
    def test_deposit_creates_audit_log(self):
        initial_balance = self.account.balance
        deposit_amount = Decimal('500.00')
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=deposit_amount,
            transaction_type=DEPOSIT,
            balance_after_transaction=initial_balance + deposit_amount
        )
        
        self.account.balance += deposit_amount
        self.account.save()
        
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            transaction=transaction,
            operation_type=DEPOSIT,
            amount=deposit_amount,
            balance_before=initial_balance,
            balance_after=self.account.balance,
            description='Test deposit'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.account, self.account)
        self.assertEqual(audit_log.amount, deposit_amount)
        self.assertEqual(audit_log.balance_before, initial_balance)
        self.assertEqual(audit_log.balance_after, initial_balance + deposit_amount)
        self.assertEqual(audit_log.operation_type, DEPOSIT)
    
    def test_withdrawal_creates_audit_log(self):
        initial_balance = self.account.balance
        withdrawal_amount = Decimal('200.00')
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=withdrawal_amount,
            transaction_type=WITHDRAWAL,
            balance_after_transaction=initial_balance - withdrawal_amount
        )
        
        self.account.balance -= withdrawal_amount
        self.account.save()
        
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            transaction=transaction,
            operation_type=WITHDRAWAL,
            amount=withdrawal_amount,
            balance_before=initial_balance,
            balance_after=self.account.balance,
            description='Test withdrawal'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.amount, withdrawal_amount)
        self.assertEqual(audit_log.balance_before, initial_balance)
        self.assertEqual(audit_log.balance_after, initial_balance - withdrawal_amount)
        self.assertEqual(audit_log.operation_type, WITHDRAWAL)
    
    def test_interest_calculation_creates_audit_log(self):
        self.account.initial_deposit_date = timezone.now()
        self.account.interest_start_date = timezone.now()
        self.account.save()
        
        initial_balance = self.account.balance
        interest = self.account_type.calculate_interest(initial_balance)
        
        audit_log = AuditLog.objects.create(
            user=None,
            account=self.account,
            operation_type=INTEREST,
            amount=interest,
            balance_before=initial_balance,
            balance_after=initial_balance + interest,
            description='Automated interest calculation'
        )
        
        self.assertIsNone(audit_log.user)
        self.assertEqual(audit_log.operation_type, INTEREST)
        self.assertGreater(audit_log.amount, Decimal('0'))
        self.assertEqual(audit_log.balance_after, audit_log.balance_before + audit_log.amount)
