from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import BankAccountType, UserBankAccount
from transactions.models import AuditLog, create_audit_log
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST

User = get_user_model()


class AuditLogModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
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
    
    def test_audit_log_creation(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        self.assertIsNotNone(audit_log.pk)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.account, self.account)
    
    def test_audit_log_immutability(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        
        audit_log.amount = Decimal('200.00')
        with self.assertRaises(ValueError) as context:
            audit_log.save()
        self.assertIn('cannot be modified', str(context.exception))
    
    def test_audit_log_cannot_be_deleted(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            account=self.account,
            action_type=DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00')
        )
        
        with self.assertRaises(ValueError) as context:
            audit_log.delete()
        self.assertIn('cannot be deleted', str(context.exception))
    
    def test_audit_log_for_system_operation(self):
        audit_log = AuditLog.objects.create(
            user=None,
            account=self.account,
            action_type=INTEREST,
            amount=Decimal('5.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1005.00'),
            metadata={'calculation_month': 12}
        )
        self.assertIsNone(audit_log.user)
        self.assertEqual(audit_log.action_type, INTEREST)


class CreateAuditLogFunctionTests(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.account_type = BankAccountType.objects.create(
            name='Test Savings',
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
    
    def test_create_audit_log_with_request(self):
        request = self.factory.post('/deposit/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        
        audit_log = create_audit_log(
            account=self.account,
            action_type=DEPOSIT,
            amount=Decimal('100.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1100.00'),
            user=self.user,
            request=request
        )
        
        self.assertEqual(audit_log.ip_address, '127.0.0.1')
        self.assertEqual(audit_log.user_agent, 'Mozilla/5.0')
    
    def test_create_audit_log_without_request(self):
        audit_log = create_audit_log(
            account=self.account,
            action_type=INTEREST,
            amount=Decimal('5.00'),
            balance_before=Decimal('1000.00'),
            balance_after=Decimal('1005.00'),
            user=None,
            request=None,
            metadata={'calculation_month': 12}
        )
        
        self.assertIsNone(audit_log.ip_address)
        self.assertIsNone(audit_log.user_agent)
        self.assertEqual(audit_log.metadata['calculation_month'], 12)
