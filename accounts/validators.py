import re
from django.core.exceptions import ValidationError


def clean_cpf(cpf):
    """Remove formatting from CPF."""
    return re.sub(r'[^0-9]', '', cpf)


def format_cpf(cpf):
    """Format CPF with mask XXX.XXX.XXX-XX."""
    cpf = clean_cpf(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def validate_cpf(cpf):
    """
    Validate CPF using Brazilian mod-11 algorithm.
    
    CPF format: XXX.XXX.XXX-XX where the last two digits are verification digits.
    """
    cpf = clean_cpf(cpf)
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    sum_first = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit_first = 11 - (sum_first % 11)
    if digit_first >= 10:
        digit_first = 0
    
    if int(cpf[9]) != digit_first:
        raise ValidationError('CPF inválido.')
    
    sum_second = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit_second = 11 - (sum_second % 11)
    if digit_second >= 10:
        digit_second = 0
    
    if int(cpf[10]) != digit_second:
        raise ValidationError('CPF inválido.')
    
    return cpf


def generate_account_digit(agency, account_number):
    """
    Generate account verification digit using mod-11 algorithm.
    Common in Brazilian banks.
    """
    combined = agency + account_number
    
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    sum_result = 0
    weight_index = 0
    
    for digit in reversed(combined):
        sum_result += int(digit) * weights[weight_index % len(weights)]
        weight_index += 1
    
    remainder = sum_result % 11
    digit = 11 - remainder
    
    if digit >= 10:
        digit = 0
    
    return str(digit)


def generate_agency():
    """Generate a random 4-digit agency number."""
    import random
    return f"{random.randint(1, 9999):04d}"
