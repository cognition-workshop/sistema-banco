from django.test import TestCase
from django.core.exceptions import ValidationError

from accounts.models import UserBankAccount, BankAccountType, User
from accounts.utils import calculate_dac10, validate_dac10, format_account


class DAC10TestCase(TestCase):
    def test_calculate_dac10_basic(self):
        """Test basic DAC10 calculation"""
        agency = '0001'
        account_number = '0000001'
        check_digit = calculate_dac10(agency, account_number)
        self.assertEqual(len(check_digit), 1)
        self.assertTrue(check_digit.isdigit())
    
    def test_validate_dac10_correct(self):
        """Test validation with correct check digit"""
        agency = '0001'
        account_number = '0000001'
        check_digit = calculate_dac10(agency, account_number)
        self.assertTrue(validate_dac10(agency, account_number, check_digit))
    
    def test_validate_dac10_incorrect(self):
        """Test validation with incorrect check digit"""
        agency = '0001'
        account_number = '0000001'
        check_digit = calculate_dac10(agency, account_number)
        wrong_digit = str((int(check_digit) + 1) % 10)
        self.assertFalse(validate_dac10(agency, account_number, wrong_digit))
    
    def test_format_account(self):
        """Test account formatting"""
        result = format_account('0001', '0000001', '5')
        self.assertEqual(result, '0001-0000001-5')


class UserBankAccountTestCase(TestCase):
    def setUp(self):
        self.account_type = BankAccountType.objects.create(
            name='Test Account',
            maximum_withdrawal_amount=5000.00,
            annual_interest_rate=5.00,
            interest_calculation_per_year=12
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_account_with_valid_data(self):
        """Test creating account with valid Brazilian format"""
        agency = '0001'
        account_number = '0000001'
        check_digit = calculate_dac10(agency, account_number)
        
        account = UserBankAccount.objects.create(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            agency=agency,
            account_number=account_number,
            check_digit=check_digit,
            gender='M'
        )
        
        self.assertEqual(account.agency, '0001')
        self.assertEqual(account.account_number, '0000001')
        self.assertEqual(account.check_digit, check_digit)
        self.assertEqual(account.get_formatted_account(), f'{agency}-{account_number}-{check_digit}')
    
    def test_account_validation_invalid_check_digit(self):
        """Test that invalid check digit raises validation error"""
        account = UserBankAccount(
            user=self.user,
            account_type=self.account_type,
            account_no=1000000001,
            agency='0001',
            account_number='0000001',
            check_digit='9',
            gender='M'
        )
        
        with self.assertRaises(ValidationError):
            account.full_clean()
