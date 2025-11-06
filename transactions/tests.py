import json
import logging
from io import StringIO
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount, UserAddress
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.tasks import calculate_interest


class StructuredLoggingTestCase(TestCase):
    """Base test case with utilities for testing structured logging"""

    def setUp(self):
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.transactions_logger = logging.getLogger('transactions')
        self.transactions_logger.addHandler(self.handler)
        self.transactions_logger.setLevel(logging.INFO)
        
        self.accounts_logger = logging.getLogger('accounts')
        self.accounts_logger.addHandler(self.handler)
        self.accounts_logger.setLevel(logging.INFO)
        
        self.savings_type = BankAccountType.objects.create(
            name="Test Savings Account",
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.00,
            interest_calculation_per_year=12
        )
        
        self.demo_user = User.objects.create_user(
            email='demo@example.com',
            password='demo123',
            first_name='Test',
            last_name='User'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.demo_user,
            account_type=self.savings_type,
            account_no=1001,
            gender='M',
            birth_date='1990-01-01',
            balance=1000.00,
            initial_deposit_date=timezone.now() - relativedelta(months=1),
            interest_start_date=timezone.now() + relativedelta(months=1)
        )
        
        self.address = UserAddress.objects.create(
            user=self.demo_user,
            street_address='123 Test St',
            city='Test City',
            postal_code=12345,
            country='Test Country'
        )
        
        self.client = Client()

    def tearDown(self):
        self.transactions_logger.removeHandler(self.handler)
        self.accounts_logger.removeHandler(self.handler)
        self.handler.close()

    def get_log_records(self):
        """Parse JSON log records from the log stream"""
        self.log_stream.seek(0)
        records = []
        for line in self.log_stream:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    def assert_log_contains_fields(self, log_record, expected_fields):
        """Assert that a log record contains all expected fields"""
        for field, expected_value in expected_fields.items():
            self.assertIn(field, log_record, f"Field '{field}' not found in log record")
            if expected_value is not None:
                actual_value = log_record[field]
                if isinstance(expected_value, Decimal):
                    actual_value = Decimal(actual_value)
                self.assertEqual(actual_value, expected_value, 
                               f"Field '{field}' has unexpected value")


class DepositLoggingTests(StructuredLoggingTestCase):
    """Test structured logging for deposit operations"""

    def test_successful_deposit_logs_structured_data(self):
        """Test that successful deposits create structured JSON logs with all required fields"""
        initial_balance = self.account.balance
        deposit_amount = Decimal('500.00')
        
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': deposit_amount}
        )
        
        self.assertEqual(response.status_code, 302)
        
        log_records = self.get_log_records()
        deposit_logs = [r for r in log_records if r.get('message') == 'Deposit completed successfully']
        
        self.assertGreater(len(deposit_logs), 0, "No deposit success log found")
        
        deposit_log = deposit_logs[0]
        self.assert_log_contains_fields(deposit_log, {
            'level': 'INFO',
            'logger': 'transactions',
            'user_email': 'demo@example.com',
            'account_no': 1001,
            'amount': deposit_amount,
            'transaction_type': 'DEPOSIT',
            'balance_after': initial_balance + deposit_amount
        })
        
        self.assertIn('timestamp', deposit_log)
        self.assertIn('module', deposit_log)
        self.assertIn('function', deposit_log)

    def test_deposit_without_account_logs_warning(self):
        """Test that deposit attempts without account log warnings"""
        self.account.delete()
        
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('100.00')}
        )
        
        log_records = self.get_log_records()
        warning_logs = [r for r in log_records if 'no account found' in r.get('message', '')]
        
        self.assertGreater(len(warning_logs), 0, "No warning log found for missing account")
        
        warning_log = warning_logs[0]
        self.assertEqual(warning_log['level'], 'WARNING')
        self.assertEqual(warning_log['transaction_type'], 'DEPOSIT')


class WithdrawalLoggingTests(StructuredLoggingTestCase):
    """Test structured logging for withdrawal operations"""

    def test_successful_withdrawal_logs_structured_data(self):
        """Test that successful withdrawals create structured JSON logs"""
        initial_balance = self.account.balance
        withdrawal_amount = Decimal('200.00')
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': withdrawal_amount}
        )
        
        self.assertEqual(response.status_code, 302)
        
        log_records = self.get_log_records()
        withdrawal_logs = [r for r in log_records if r.get('message') == 'Withdrawal completed successfully']
        
        self.assertGreater(len(withdrawal_logs), 0, "No withdrawal success log found")
        
        withdrawal_log = withdrawal_logs[0]
        self.assert_log_contains_fields(withdrawal_log, {
            'level': 'INFO',
            'logger': 'transactions',
            'user_email': 'demo@example.com',
            'account_no': 1001,
            'amount': withdrawal_amount,
            'transaction_type': 'WITHDRAWAL',
            'balance_after': initial_balance - withdrawal_amount
        })

    def test_withdrawal_without_account_logs_warning(self):
        """Test that withdrawal attempts without account log warnings"""
        self.account.delete()
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': Decimal('100.00')}
        )
        
        log_records = self.get_log_records()
        warning_logs = [r for r in log_records if 'no account found' in r.get('message', '')]
        
        self.assertGreater(len(warning_logs), 0, "No warning log found for missing account")
        
        warning_log = warning_logs[0]
        self.assertEqual(warning_log['level'], 'WARNING')
        self.assertEqual(warning_log['transaction_type'], 'WITHDRAWAL')

    def test_insufficient_balance_withdrawal_logs_warning(self):
        """Test that withdrawals with insufficient balance log warnings"""
        self.account.balance = Decimal('50.00')
        self.account.save()
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': Decimal('100.00')}
        )
        
        log_records = self.get_log_records()
        warning_logs = [r for r in log_records if 'insufficient balance' in r.get('message', '').lower()]
        
        self.assertGreater(len(warning_logs), 0, "No warning log found for insufficient balance")


class InterestCalculationLoggingTests(StructuredLoggingTestCase):
    """Test structured logging for interest calculation task"""

    def test_interest_calculation_logs_start_and_completion(self):
        """Test that interest calculation task logs start and completion"""
        self.account.interest_start_date = timezone.now() - relativedelta(days=1)
        self.account.save()
        
        with patch('transactions.tasks.timezone') as mock_timezone:
            mock_now = timezone.now()
            mock_timezone.now.return_value = mock_now
            
            result = calculate_interest()
        
        log_records = self.get_log_records()
        
        start_logs = [r for r in log_records if r.get('message') == 'Starting interest calculation task']
        self.assertGreater(len(start_logs), 0, "No start log found")
        
        completion_logs = [r for r in log_records if r.get('message') == 'Interest calculation task completed']
        self.assertGreater(len(completion_logs), 0, "No completion log found")

    def test_interest_calculation_logs_each_account(self):
        """Test that interest calculation logs details for each processed account"""
        self.account.interest_start_date = timezone.now() - relativedelta(days=1)
        self.account.initial_deposit_date = timezone.now() - relativedelta(months=2)
        self.account.save()
        
        initial_balance = self.account.balance
        
        with patch('transactions.tasks.timezone') as mock_timezone:
            current_month = self.account.interest_start_date.month
            mock_now = self.account.interest_start_date.replace(day=15)
            mock_timezone.now.return_value = mock_now
            
            result = calculate_interest()
        
        log_records = self.get_log_records()
        
        interest_logs = [r for r in log_records if r.get('message') == 'Interest calculated and applied']
        
        if len(interest_logs) > 0:
            interest_log = interest_logs[0]
            self.assert_log_contains_fields(interest_log, {
                'level': 'INFO',
                'logger': 'transactions',
                'account_no': 1001,
                'user_email': 'demo@example.com',
                'transaction_type': 'INTEREST',
            })
            
            self.assertIn('amount', interest_log)
            self.assertIn('balance_after', interest_log)

    def test_interest_calculation_logs_summary(self):
        """Test that interest calculation logs summary statistics"""
        self.account.interest_start_date = timezone.now() - relativedelta(days=1)
        self.account.initial_deposit_date = timezone.now() - relativedelta(months=2)
        self.account.save()
        
        with patch('transactions.tasks.timezone') as mock_timezone:
            mock_now = self.account.interest_start_date.replace(day=15)
            mock_timezone.now.return_value = mock_now
            
            result = calculate_interest()
        
        log_records = self.get_log_records()
        
        completion_logs = [r for r in log_records if r.get('message') == 'Interest calculation task completed']
        
        if len(completion_logs) > 0:
            completion_log = completion_logs[0]
            self.assertIn('accounts_processed', completion_log)
            self.assertIn('total_transactions', completion_log)


class ErrorHandlingLoggingTests(StructuredLoggingTestCase):
    """Test structured logging for error scenarios"""

    @patch('transactions.views.transaction')
    def test_database_error_during_deposit_logs_error(self, mock_transaction):
        """Test that database errors during deposit are logged"""
        from django.db import OperationalError
        
        mock_transaction.atomic.side_effect = OperationalError("Database connection failed")
        
        response = self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('100.00')}
        )
        
        log_records = self.get_log_records()
        
        error_logs = [r for r in log_records if 'error' in r.get('message', '').lower()]
        self.assertGreater(len(error_logs), 0, "No error log found for database error")

    @patch('transactions.views.transaction')
    def test_database_error_during_withdrawal_logs_error(self, mock_transaction):
        """Test that database errors during withdrawal are logged"""
        from django.db import OperationalError
        
        mock_transaction.atomic.side_effect = OperationalError("Database connection failed")
        
        response = self.client.post(
            reverse('transactions:withdraw_money'),
            {'amount': Decimal('50.00')}
        )
        
        log_records = self.get_log_records()
        
        error_logs = [r for r in log_records if 'error' in r.get('message', '').lower()]
        self.assertGreater(len(error_logs), 0, "No error log found for database error")


class LogFormatTests(StructuredLoggingTestCase):
    """Test that all logs follow the correct JSON structure"""

    def test_all_logs_are_valid_json(self):
        """Test that all log output is valid JSON"""
        self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('100.00')}
        )
        
        self.log_stream.seek(0)
        for line in self.log_stream:
            line = line.strip()
            if line:
                try:
                    log_record = json.loads(line)
                    self.assertIsInstance(log_record, dict)
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in log output: {line}\nError: {e}")

    def test_logs_contain_required_base_fields(self):
        """Test that all logs contain required base fields"""
        self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('100.00')}
        )
        
        required_fields = ['timestamp', 'level', 'logger', 'message', 'module', 'function', 'line']
        
        log_records = self.get_log_records()
        for record in log_records:
            for field in required_fields:
                self.assertIn(field, record, f"Required field '{field}' missing from log record")

    def test_timestamp_format_is_iso8601(self):
        """Test that timestamps follow ISO 8601 format"""
        self.client.post(
            reverse('transactions:deposit_money'),
            {'amount': Decimal('100.00')}
        )
        
        log_records = self.get_log_records()
        for record in log_records:
            timestamp = record.get('timestamp', '')
            self.assertTrue(
                timestamp.endswith('Z') and 'T' in timestamp,
                f"Timestamp '{timestamp}' is not in ISO 8601 format"
            )
