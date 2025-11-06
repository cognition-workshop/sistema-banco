from django.core.exceptions import ValidationError
from validate_docbr import CPF


def validate_cpf(value):
    cpf = CPF()
    
    if not value:
        return
    
    cpf_clean = ''.join(filter(str.isdigit, value))
    
    if not cpf.validate(cpf_clean):
        raise ValidationError(
            'CPF inválido. Por favor, insira um CPF válido no formato XXX.XXX.XXX-XX',
            code='invalid_cpf'
        )
    
    return cpf_clean


def format_cpf(value):
    if not value:
        return value
    
    cpf_clean = ''.join(filter(str.isdigit, value))
    
    if len(cpf_clean) == 11:
        return f'{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}'
    
    return value
