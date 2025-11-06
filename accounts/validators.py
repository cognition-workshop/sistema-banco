import re
from django.core.exceptions import ValidationError


def validate_cpf(cpf):
    """Validate Brazilian CPF number."""
    cpf = re.sub(r'\D', '', cpf)
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11)
    if digit1 >= 10:
        digit1 = 0
    
    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11)
    if digit2 >= 10:
        digit2 = 0
    
    if cpf[-2:] != f"{digit1}{digit2}":
        raise ValidationError('CPF inválido')
    
    return cpf


def format_cpf(cpf):
    """Format CPF to XXX.XXX.XXX-XX pattern."""
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
