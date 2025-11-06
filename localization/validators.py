from django.core.exceptions import ValidationError
from validate_docbr import CPF


def validate_cpf(value):
    """
    Valida CPF brasileiro usando validate-docbr
    """
    cpf_validator = CPF()
    
    if not cpf_validator.validate(value):
        raise ValidationError(
            'CPF inválido. Por favor, insira um CPF válido no formato XXX.XXX.XXX-XX ou apenas números.'
        )
