import re
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_postal_code_format(value):
    """Valida formato de CEP brasileiro (XXXXX-XXX ou XXXXXXXX)."""
    pattern = r'^\d{5}-?\d{3}$'
    if not re.match(pattern, str(value)):
        raise ValidationError(
            'Formato de CEP inválido. Use o formato: XXXXX-XXX ou XXXXXXXX'
        )


def validate_name_format(value):
    """Valida que o nome contém apenas letras e espaços."""
    if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', value):
        raise ValidationError(
            'O nome deve conter apenas letras e espaços.'
        )


def validate_minimum_age(value):
    """Valida que o usuário tem pelo menos 18 anos."""
    today = date.today()
    age = relativedelta(today, value).years
    if age < 18:
        raise ValidationError(
            'Você deve ter pelo menos 18 anos para abrir uma conta.'
        )


def validate_allowed_address_chars(value):
    """Valida caracteres permitidos em endereços."""
    if not re.match(r'^[A-Za-z0-9À-ÿ\s,.\-/]+$', value):
        raise ValidationError(
            'O endereço contém caracteres inválidos.'
        )


VALID_COUNTRIES = [
    'Brasil', 'Brazil', 'Argentina', 'Chile', 'Uruguai', 'Paraguai',
    'Portugal', 'Estados Unidos', 'United States', 'Canadá', 'México'
]


postal_code_validator = RegexValidator(
    regex=r'^\d{5}-?\d{3}$',
    message='Formato de CEP inválido. Use o formato: XXXXX-XXX'
)
