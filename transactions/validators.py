from decimal import Decimal
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_minimum_deposit(value):
    """Valida valor mínimo de depósito"""
    min_amount = Decimal(str(settings.MINIMUM_DEPOSIT_AMOUNT))
    if value < min_amount:
        raise ValidationError(f"Valor mínimo para depósito é {min_amount} $")


def validate_minimum_withdrawal(value):
    """Valida valor mínimo de saque"""
    min_amount = Decimal(str(settings.MINIMUM_WITHDRAWAL_AMOUNT))
    if value < min_amount:
        raise ValidationError(f"Valor mínimo para saque é {min_amount} $")
