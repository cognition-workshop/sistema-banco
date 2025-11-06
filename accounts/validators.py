from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cpf(value):
    """
    Validates Brazilian CPF (Cadastro de Pessoas Físicas) number.
    
    CPF must be exactly 11 digits and pass the check digit verification.
    """
    cpf = ''.join(filter(str.isdigit, str(value)))
    
    if len(cpf) != 11:
        raise ValidationError(
            _('CPF must have exactly 11 digits.'),
            code='invalid_cpf_length'
        )
    
    if cpf == cpf[0] * 11:
        raise ValidationError(
            _('CPF cannot have all digits the same.'),
            code='invalid_cpf_pattern'
        )
    
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto1 = soma1 % 11
    dig1 = 0 if resto1 in (0, 1) else 11 - resto1
    
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto2 = soma2 % 11
    dig2 = 0 if resto2 in (0, 1) else 11 - resto2
    
    if not (int(cpf[9]) == dig1 and int(cpf[10]) == dig2):
        raise ValidationError(
            _('Invalid CPF number.'),
            code='invalid_cpf'
        )
