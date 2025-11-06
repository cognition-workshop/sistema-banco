import re
from django.core.exceptions import ValidationError


def validate_cpf(value):
    """
    Validate Brazilian CPF (Cadastro de Pessoas Físicas).
    Format: XXX.XXX.XXX-XX or XXXXXXXXXXX
    """
    cpf = re.sub(r'[^0-9]', '', value)
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')
    
    if cpf in [str(i) * 11 for i in range(10)]:
        raise ValidationError('CPF inválido.')
    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        raise ValidationError('CPF inválido.')
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[10]) != digito2:
        raise ValidationError('CPF inválido.')
    
    return value
