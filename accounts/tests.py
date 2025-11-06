from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.validators import validate_cpf
from accounts.utils import calcular_digito_verificador, formatar_conta_brasileira
from accounts.models import User, UserBankAccount, BankAccountType


class CPFValidationTests(TestCase):
    def test_valid_cpf(self):
        """Test CPF validation with valid CPFs"""
        valid_cpfs = [
            '11144477735',
        ]
        for cpf in valid_cpfs:
            try:
                validate_cpf(cpf)
            except ValidationError:
                self.fail(f"Valid CPF {cpf} raised ValidationError")
    
    def test_invalid_cpf_sequences(self):
        """Test CPF validation rejects invalid sequences"""
        invalid_cpfs = [
            '00000000000',
            '11111111111',
        ]
        for cpf in invalid_cpfs:
            with self.assertRaises(ValidationError):
                validate_cpf(cpf)
    
    def test_invalid_cpf_wrong_digits(self):
        """Test CPF validation rejects wrong verification digits"""
        with self.assertRaises(ValidationError):
            validate_cpf('11144477700')


class AccountVerificationDigitTests(TestCase):
    def test_digit_calculation(self):
        """Test verification digit calculation"""
        agencia = '0001'
        conta = '0000000123'
        digito = calcular_digito_verificador(agencia, conta)
        self.assertIsInstance(digito, str)
        self.assertEqual(len(digito), 1)
    
    def test_account_formatting(self):
        """Test Brazilian account format"""
        formatted = formatar_conta_brasileira('0001', '123', '5')
        self.assertEqual(formatted, '0001.0000000123-5')
