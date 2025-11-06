import re
from django.core.exceptions import ValidationError


def validate_cpf(value):
    cpf = re.sub(r'[^0-9]', '', value)
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    def calculate_digit(cpf_partial, weight_start):
        sum_val = sum(int(cpf_partial[i]) * (weight_start - i) for i in range(len(cpf_partial)))
        remainder = sum_val % 11
        return 0 if remainder < 2 else 11 - remainder
    
    if int(cpf[9]) != calculate_digit(cpf[:9], 10):
        raise ValidationError('CPF inválido')
    
    if int(cpf[10]) != calculate_digit(cpf[:10], 11):
        raise ValidationError('CPF inválido')
    
    return cpf


def format_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return cpf
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}'
