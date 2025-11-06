from django.core.exceptions import ValidationError
import re

def validate_cpf(value):
    """
    Validates Brazilian CPF (Cadastro de Pessoas Físicas).
    CPF format: XXX.XXX.XXX-XX or XXXXXXXXXXX (11 digits)
    """
    cpf = re.sub(r'[^0-9]', '', str(value))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    sum_digits = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_digit = (sum_digits * 10) % 11
    if first_digit == 10:
        first_digit = 0
    if first_digit != int(cpf[9]):
        raise ValidationError('CPF inválido.')
    
    sum_digits = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_digit = (sum_digits * 10) % 11
    if second_digit == 10:
        second_digit = 0
    if second_digit != int(cpf[10]):
        raise ValidationError('CPF inválido.')
    
    return value
