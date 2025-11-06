import json
import logging
from io import StringIO
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from accounts.models import User, BankAccountType, UserBankAccount, UserAddress


class AuthenticationLoggingTestCase(TestCase):
    """Base test case for authentication logging tests"""

    def setUp(self):
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setFormatter(logging.Formatter('%(message)s'))
        
        self.accounts_logger = logging.getLogger('accounts')
        self.accounts_logger.addHandler(self.handler)
        self.accounts_logger.setLevel(logging.INFO)
        
        self.savings_type = BankAccountType.objects.create(
            name="Test Savings Account",
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.00,
            interest_calculation_per_year=12
        )
        
        self.client = Client()

    def tearDown(self):
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


class UserRegistrationLoggingTests(AuthenticationLoggingTestCase):
    """Test structured logging for user registration"""

    def test_successful_registration_logs_user_info(self):
        """Test that successful user registration creates structured logs"""
        registration_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'password1': 'testpass123!@#',
            'password2': 'testpass123!@#',
            'account_type': self.savings_type.id,
            'gender': 'M',
            'birth_date': '1990-01-01',
            'street_address': '123 Test St',
            'city': 'Test City',
            'postal_code': 12345,
            'country': 'Test Country'
        }
        
        response = self.client.post(
            reverse('accounts:user_registration'),
            registration_data
        )
        
        log_records = self.get_log_records()
        success_logs = [r for r in log_records if r.get('message') == 'New user registered successfully']
        
        self.assertGreater(len(success_logs), 0, "No registration success log found")
        
        success_log = success_logs[0]
        self.assertEqual(success_log['level'], 'INFO')
        self.assertEqual(success_log['logger'], 'accounts')
        self.assertEqual(success_log['user_email'], 'john.doe@test.com')
        self.assertIn('account_no', success_log)
        self.assertIn('timestamp', success_log)

    def test_failed_registration_logs_validation_errors(self):
        """Test that failed registration logs validation errors"""
        invalid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'password1': 'pass',
            'password2': 'different',
        }
        
        response = self.client.post(
            reverse('accounts:user_registration'),
            invalid_data
        )
        
        log_records = self.get_log_records()
        warning_logs = [r for r in log_records if 'validation error' in r.get('message', '').lower()]
        
        self.assertGreater(len(warning_logs), 0, "No warning log found for failed registration")
        
        warning_log = warning_logs[0]
        self.assertEqual(warning_log['level'], 'WARNING')
        self.assertEqual(warning_log['logger'], 'accounts')


class UserLoginLoggingTests(AuthenticationLoggingTestCase):
    """Test structured logging for user login"""

    def setUp(self):
        super().setUp()
        
        self.test_user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.test_user,
            account_type=self.savings_type,
            account_no=2001,
            gender='M',
            birth_date='1990-01-01',
            balance=1000.00
        )

    def test_successful_login_logs_user_email(self):
        """Test that successful login creates structured logs with user email"""
        login_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(
            reverse('accounts:user_login'),
            login_data
        )
        
        log_records = self.get_log_records()
        login_logs = [r for r in log_records if r.get('message') == 'User logged in successfully']
        
        self.assertGreater(len(login_logs), 0, "No login success log found")
        
        login_log = login_logs[0]
        self.assertEqual(login_log['level'], 'INFO')
        self.assertEqual(login_log['logger'], 'accounts')
        self.assertEqual(login_log['user_email'], 'test@example.com')
        self.assertIn('timestamp', login_log)


class UserLogoutLoggingTests(AuthenticationLoggingTestCase):
    """Test structured logging for user logout"""

    def setUp(self):
        super().setUp()
        
        self.test_user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.test_user,
            account_type=self.savings_type,
            account_no=2001,
            gender='M',
            birth_date='1990-01-01',
            balance=1000.00
        )

    def test_logout_logs_user_email(self):
        """Test that logout creates structured logs with user email"""
        self.client.login(username='test@example.com', password='testpass123')
        
        response = self.client.get(reverse('accounts:user_logout'))
        
        log_records = self.get_log_records()
        logout_logs = [r for r in log_records if r.get('message') == 'User logged out']
        
        self.assertGreater(len(logout_logs), 0, "No logout log found")
        
        logout_log = logout_logs[0]
        self.assertEqual(logout_log['level'], 'INFO')
        self.assertEqual(logout_log['logger'], 'accounts')
        self.assertEqual(logout_log['user_email'], 'test@example.com')

    def test_logout_without_authenticated_user_no_log(self):
        """Test that logout without authenticated user doesn't log user email"""
        response = self.client.get(reverse('accounts:user_logout'))
        
        log_records = self.get_log_records()
        logout_logs = [r for r in log_records if r.get('message') == 'User logged out']
        
        self.assertEqual(len(logout_logs), 0, "Logout log found for unauthenticated user")


class AuthenticationLogFormatTests(AuthenticationLoggingTestCase):
    """Test that authentication logs follow correct JSON structure"""

    def setUp(self):
        super().setUp()
        
        self.test_user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.account = UserBankAccount.objects.create(
            user=self.test_user,
            account_type=self.savings_type,
            account_no=2001,
            gender='M',
            birth_date='1990-01-01',
            balance=1000.00
        )

    def test_authentication_logs_are_valid_json(self):
        """Test that all authentication log output is valid JSON"""
        self.client.post(
            reverse('accounts:user_login'),
            {'username': 'test@example.com', 'password': 'testpass123'}
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

    def test_authentication_logs_contain_base_fields(self):
        """Test that authentication logs contain required base fields"""
        self.client.post(
            reverse('accounts:user_login'),
            {'username': 'test@example.com', 'password': 'testpass123'}
        )
        
        required_fields = ['timestamp', 'level', 'logger', 'message', 'module', 'function']
        
        log_records = self.get_log_records()
        for record in log_records:
            for field in required_fields:
                self.assertIn(field, record, f"Required field '{field}' missing from log record")
