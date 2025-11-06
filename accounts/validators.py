from django.core.exceptions import ValidationError
import re


def validate_cpf_format(value):
    """
    Validates CPF format: XXX.XXX.XXX-XX or XXXXXXXXXXX
    """
    cpf = re.sub(r'[^\d]', '', str(value))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve conter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    return cpf


def validate_cpf_digits(value):
    """
    Validates CPF verification digits using Brazilian algorithm
    """
    cpf = validate_cpf_format(value)
    
    sum_first = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_digit = (sum_first * 10 % 11) % 10
    
    if int(cpf[9]) != first_digit:
        raise ValidationError('Dígitos verificadores do CPF são inválidos')
    
    sum_second = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_digit = (sum_second * 10 % 11) % 10
    
    if int(cpf[10]) != second_digit:
        raise ValidationError('Dígitos verificadores do CPF são inválidos')
    
    return cpf


def format_cpf(cpf):
    """
    Formats CPF as XXX.XXX.XXX-XX
    """
    cpf = re.sub(r'[^\d]', '', str(cpf))
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    return cpf


def calculate_account_digit(agency, account_number):
    """
    Calculates check digit for Brazilian bank account using modulo 11
    """
    combined = f'{agency:04d}{account_number:08d}'
    
    weights = [9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6]
    total = sum(int(combined[i]) * weights[i] for i in range(12))
    
    remainder = total % 11
    digit = 0 if remainder < 2 else 11 - remainder
    
    return digit


def validate_account_digit(agency, account_number, digit):
    """
    Validates Brazilian bank account check digit
    """
    calculated = calculate_account_digit(agency, account_number)
    if calculated != digit:
        raise ValidationError(f'Dígito verificador incorreto. Esperado: {calculated}')
