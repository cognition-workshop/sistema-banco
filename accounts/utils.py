from django.utils import timezone


def calcular_digito_verificador(agencia, conta):
    """
    Calculate verification digit using module 11 algorithm
    (standard Brazilian banking algorithm).
    """
    numero = agencia + conta.zfill(10)
    
    soma = 0
    peso = 2
    for digito in reversed(numero):
        soma += int(digito) * peso
        peso += 1
        if peso > 9:
            peso = 2
    
    resto = soma % 11
    digito = 0 if resto < 2 else 11 - resto
    
    return str(digito)


def formatar_conta_brasileira(agencia, conta, digito):
    """
    Format account in Brazilian standard: XXXX.YYYYYYYYYY-D
    """
    return f"{agencia}.{conta.zfill(10)}-{digito}"


def anonymize_user(user):
    """
    Anonymize user data for LGPD right to be forgotten
    """
    user.first_name = f"ANONYMIZED_{user.id}"
    user.last_name = "USER"
    user.email = f"anonymized_{user.id}@deleted.local"
    user.cpf = None
    user.is_active = False
    user.save()
    
    if hasattr(user, 'account'):
        account = user.account
        account.gender = 'X'
        account.birth_date = None
        account.save()
