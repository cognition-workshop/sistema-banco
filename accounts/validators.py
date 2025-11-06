import re
from django.core.exceptions import ValidationError


def validate_cpf(value):
    """
    Valida CPF brasileiro (formato: 000.000.000-00 ou 00000000000)
    """
    cpf = re.sub(r"[^0-9]", "", str(value))

    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos")

    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido")

    def calculate_digit(cpf_partial):
        total = sum(
            (len(cpf_partial) + 1 - i) * int(digit)
            for i, digit in enumerate(cpf_partial)
        )
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    if calculate_digit(cpf[:9]) != int(cpf[9]):
        raise ValidationError("CPF inválido")

    if calculate_digit(cpf[:10]) != int(cpf[10]):
        raise ValidationError("CPF inválido")

    return cpf


def validate_positive_amount(value):
    """Valida que o valor é positivo"""
    if value <= 0:
        raise ValidationError("O valor deve ser maior que zero")


def validate_account_number(value):
    """Valida número de conta bancária brasileira"""
    if value < 1000000000 or value > 9999999999:
        raise ValidationError("Número de conta inválido")
