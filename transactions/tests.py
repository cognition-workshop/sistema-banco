from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import UserBankAccount, BankAccountType
from transactions.models import Transaction, AuditLog
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.tasks import calculate_interest

User = get_user_model()


class AuditLogTestCase(TestCase):
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
            account_no=1000000001,
            gender='M',
            balance=Decimal('1000.00')
        )
        
        self.client = Client()
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_deposit_creates_audit_log(self):
        initial_balance = self.account.balance
        deposit_amount = Decimal('500.00')
        
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {
                'amount': deposit_amount,
                'transaction_type': DEPOSIT
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        audit_log = AuditLog.objects.filter(
            user=self.user,
            account=self.account,
            action_type=AuditLog.DEPOSIT
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.amount, deposit_amount)
        self.assertEqual(audit_log.balance_before, initial_balance)
        self.assertEqual(audit_log.balance_after, initial_balance + deposit_amount)
        self.assertIsNotNone(audit_log.transaction)
    
    def test_withdrawal_creates_audit_log(self):
        initial_balance = self.account.balance
        withdrawal_amount = Decimal('200.00')
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {
                'amount': withdrawal_amount,
                'transaction_type': WITHDRAWAL
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        audit_log = AuditLog.objects.filter(
            user=self.user,
            account=self.account,
            action_type=AuditLog.WITHDRAWAL
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.amount, withdrawal_amount)
        self.assertEqual(audit_log.balance_before, initial_balance)
        self.assertEqual(audit_log.balance_after, initial_balance - withdrawal_amount)
        self.assertIsNotNone(audit_log.transaction)
    
    def test_interest_calculation_creates_audit_log(self):
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        now = timezone.now()
        self.account.initial_deposit_date = now - relativedelta(months=2)
        self.account.interest_start_date = now - relativedelta(days=1)
        self.account.save()
        
        initial_balance = self.account.balance
        
        calculate_interest()
        
        audit_log = AuditLog.objects.filter(
            account=self.account,
            action_type=AuditLog.INTEREST
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.balance_before, initial_balance)
        self.assertGreater(audit_log.balance_after, initial_balance)
        self.assertGreater(audit_log.amount, Decimal('0'))
        self.assertIsNotNone(audit_log.transaction)
    
    def test_audit_log_immutability_save(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=AuditLog.DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        
        audit_log.amount = Decimal('200.00')
        
        with self.assertRaises(ValueError) as context:
            audit_log.save()
        
        self.assertIn('cannot be modified', str(context.exception))
    
    def test_audit_log_immutability_delete(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=AuditLog.DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        
        with self.assertRaises(ValueError) as context:
            audit_log.delete()
        
        self.assertIn('cannot be deleted', str(context.exception))
        
        self.assertTrue(AuditLog.objects.filter(pk=audit_log.pk).exists())
    
    def test_audit_log_searchability(self):
        AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=AuditLog.DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        
        AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=AuditLog.WITHDRAWAL,
            amount=Decimal('50.00'),
            balance_before=Decimal('1100.00'),
            balance_after=Decimal('1050.00')
        )
        
        user_logs = AuditLog.objects.filter(user=self.user)
        self.assertEqual(user_logs.count(), 2)
        
        account_logs = AuditLog.objects.filter(account=self.account)
        self.assertEqual(account_logs.count(), 2)
        
        deposit_logs = AuditLog.objects.filter(action_type=AuditLog.DEPOSIT)
        self.assertEqual(deposit_logs.count(), 1)
        
        withdrawal_logs = AuditLog.objects.filter(action_type=AuditLog.WITHDRAWAL)
        self.assertEqual(withdrawal_logs.count(), 1)
