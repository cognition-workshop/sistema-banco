from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class PositiveAmountValidator(BaseValidator):
    """Validator to ensure amount is positive."""

    message = "O valor deve ser positivo"
    code = "invalid_amount"

    def compare(self, a, b):
        return a <= 0


@deconstructible
class MinimumAmountValidator(BaseValidator):
    """Validator to ensure amount meets minimum requirement."""

    message = "O valor deve ser no mínimo %(limit_value)s $"
    code = "minimum_amount"

    def compare(self, a, b):
        return a < b
