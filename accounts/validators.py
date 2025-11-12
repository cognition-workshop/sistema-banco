import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


CPF_INVALID_MSG = _("Invalid CPF")


def normalize_digits(value: str) -> str:
    """Remove all non-digit characters from a string."""
    return re.sub(r"\D", "", value or "")


def validate_cpf(value: str):
    """
    Validate Brazilian CPF number.
    
    CPF must be 11 digits and pass the check digit algorithm.
    Accepts input with or without formatting (e.g., "123.456.789-00" or "12345678900").
    """
    if not value:
        return
    
    digits = normalize_digits(value)
    
    if len(digits) != 11 or digits == digits[0] * 11:
        raise ValidationError(CPF_INVALID_MSG)
    
    def calc_check(nums, multipliers):
        s = sum(int(n) * m for n, m in zip(nums, multipliers))
        r = s % 11
        return "0" if r < 2 else str(11 - r)
    
    first_check = calc_check(digits[:9], range(10, 1, -1))
    second_check = calc_check(digits[:9] + first_check, range(11, 1, -1))
    
    if digits[-2:] != first_check + second_check:
        raise ValidationError(CPF_INVALID_MSG)
