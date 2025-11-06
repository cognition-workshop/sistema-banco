"""Utility functions for account management"""


def calcular_digito_verificador(agencia, conta):
    """
    Calculate check digit using módulo 11 algorithm (standard for Brazilian banking).
    
    Args:
        agencia: 4-digit agency number (string or int)
        conta: Account number (string or int)
    
    Returns:
        str: Check digit (0-9 or X for 10)
    """
    numero_completo = str(agencia) + str(conta)
    
    soma = 0
    multiplicador = 2
    
    for digito in reversed(numero_completo):
        soma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 9 else 2
    
    resto = soma % 11
    digito = 11 - resto
    
    if digito >= 10:
        return 'X'
    return str(digito)
