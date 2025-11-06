from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cpf(value):
    """
    Validates Brazilian CPF (Cadastro de Pessoas Físicas).
    CPF must have exactly 11 digits and pass the verification digit check.
    """
    if not value:
        raise ValidationError(_('CPF é obrigatório.'))
    
    cpf = ''.join(filter(str.isdigit, value))
    
    if len(cpf) != 11:
        raise ValidationError(_('CPF deve ter exatamente 11 dígitos.'))
    
    if cpf == cpf[0] * 11:
        raise ValidationError(_('CPF inválido.'))
    
    def calculate_digit(cpf_partial, position):
        sum_value = 0
        for i, digit in enumerate(cpf_partial):
            sum_value += int(digit) * (position - i)
        remainder = sum_value % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_digit = calculate_digit(cpf[:9], 10)
    if first_digit != int(cpf[9]):
        raise ValidationError(_('CPF inválido.'))
    
    second_digit = calculate_digit(cpf[:10], 11)
    if second_digit != int(cpf[10]):
        raise ValidationError(_('CPF inválido.'))
    
    return value
