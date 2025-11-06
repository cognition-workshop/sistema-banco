from django.test import TestCase
from django.core.exceptions import ValidationError
from localization.validators import validate_cpf


class CPFValidatorTestCase(TestCase):
    """Testes para validador de CPF"""
    
    def test_cpf_valido(self):
        """Testa CPF válido"""
        cpfs_validos = [
            '111.444.777-35',
            '11144477735',
        ]
        for cpf in cpfs_validos:
            try:
                validate_cpf(cpf)
            except ValidationError:
                self.fail(f'CPF {cpf} deveria ser válido')
    
    def test_cpf_invalido(self):
        """Testa CPF inválido"""
        cpfs_invalidos = [
            '111.111.111-11',
            '12345678901',
            'abc.def.ghi-jk',
            '',
        ]
        for cpf in cpfs_invalidos:
            with self.assertRaises(ValidationError):
                validate_cpf(cpf)
