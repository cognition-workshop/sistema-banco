from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime

from accounts.models import UserBankAccount, BankAccountType, UserAddress
from transactions.models import Transaction, AuditLog
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.forms import WithdrawForm, DepositForm

User = get_user_model()


class WithdrawFormTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
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

    def test_withdraw_form_prevents_negative_balance(self):
        form = WithdrawForm(
            data={'amount': Decimal('1500.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Insufficient balance', str(form.errors))

    def test_withdraw_form_allows_valid_withdrawal(self):
        form = WithdrawForm(
            data={'amount': Decimal('500.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_withdraw_form_respects_minimum_amount(self):
        form = WithdrawForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())

    def test_withdraw_form_respects_maximum_amount(self):
        self.account.balance = Decimal('10000.00')
        self.account.save()
        form = WithdrawForm(
            data={'amount': Decimal('6000.00')},
            initial={'transaction_type': WITHDRAWAL},
            account=self.account
        )
        self.assertFalse(form.is_valid())


class DepositFormTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
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

    def test_deposit_form_allows_valid_deposit(self):
        form = DepositForm(
            data={'amount': Decimal('500.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertTrue(form.is_valid())

    def test_deposit_form_respects_minimum_amount(self):
        form = DepositForm(
            data={'amount': Decimal('5.00')},
            initial={'transaction_type': DEPOSIT},
            account=self.account
        )
        self.assertFalse(form.is_valid())


class WithdrawViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
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
        UserAddress.objects.create(
            user=self.user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )

    def test_withdraw_view_requires_authentication(self):
        response = self.client.get(reverse('transactions:withdraw_money'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_withdraw_view_atomic_transaction(self):
        self.client.login(email='test@example.com', password='testpass123')
        initial_balance = self.account.balance
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': Decimal('100.00'), 'transaction_type': WITHDRAWAL}
        )
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance - Decimal('100.00'))
        self.assertEqual(response.status_code, 302)

    def test_withdraw_creates_audit_log(self):
        self.client.login(email='test@example.com', password='testpass123')
        
        self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': Decimal('100.00'), 'transaction_type': WITHDRAWAL}
        )
        
        audit_log = AuditLog.objects.filter(action='WITHDRAWAL').first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.model_name, 'UserBankAccount')


class DepositViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('5.0'),
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
        UserAddress.objects.create(
            user=self.user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )

    def test_deposit_view_requires_authentication(self):
        response = self.client.get(reverse('transactions:deposit_money'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_deposit_view_increases_balance(self):
        self.client.login(email='test@example.com', password='testpass123')
        initial_balance = self.account.balance
        
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('500.00'), 'transaction_type': DEPOSIT}
        )
        
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_balance + Decimal('500.00'))

    def test_deposit_creates_audit_log(self):
        self.client.login(email='test@example.com', password='testpass123')
        
        self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('500.00'), 'transaction_type': DEPOSIT}
        )
        
        audit_log = AuditLog.objects.filter(action='DEPOSIT').first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.user, self.user)


class InterestCalculationTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Savings',
            maximum_withdrawal_amount=Decimal('5000.00'),
            annual_interest_rate=Decimal('12.0'),
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
            balance=Decimal('1000.00'),
            initial_deposit_date=timezone.now().date(),
            interest_start_date=timezone.now().date()
        )

    def test_interest_calculation_logic(self):
        interest = self.account.account_type.calculate_interest(Decimal('1000.00'))
        self.assertGreater(interest, Decimal('0'))
        self.assertEqual(interest, Decimal('10.00'))


class AuditLogTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_audit_log_creation(self):
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='TEST_ACTION',
            model_name='TestModel',
            object_id=1,
            changes={'field': 'value'},
            description='Test audit log'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'TEST_ACTION')
        self.assertEqual(audit_log.model_name, 'TestModel')

    def test_audit_log_ordering(self):
        AuditLog.objects.create(
            user=self.user,
            action='FIRST',
            model_name='TestModel'
        )
        AuditLog.objects.create(
            user=self.user,
            action='SECOND',
            model_name='TestModel'
        )
        
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0].action, 'SECOND')
        self.assertEqual(logs[1].action, 'FIRST')
