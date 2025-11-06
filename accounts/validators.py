import re
from django.core.exceptions import ValidationError


def validate_cpf(value):
    """Validate Brazilian CPF number using check digits algorithm."""
    cpf = re.sub(r'[^0-9]', '', str(value))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    if int(cpf[9]) != digit1:
        raise ValidationError('CPF inválido.')
    
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    if int(cpf[10]) != digit2:
        raise ValidationError('CPF inválido.')
    
    return cpf
