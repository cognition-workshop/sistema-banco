import random

def generate_agencia():
    """Generate a 4-digit agency number."""
    return str(random.randint(1000, 9999))

def generate_conta():
    """Generate an 8-digit account number."""
    return str(random.randint(10000000, 99999999))

def calculate_digito_verificador(agencia, conta):
    """
    Calculate check digit for Brazilian bank account.
    Using modulo 11 algorithm (common in Brazilian banks).
    """
    combined = agencia + conta
    
    weights = [9, 8, 7, 6, 5, 4, 3, 2, 9, 8, 7, 6]
    sum_digits = sum(int(combined[i]) * weights[i] for i in range(len(combined)))
    
    remainder = sum_digits % 11
    if remainder == 0 or remainder == 1:
        return '0'
    else:
        return str(11 - remainder)

def format_account_number(agencia, conta, digito):
    """Format account number as XXXX-XXXXXXXX-X"""
    return f"{agencia}-{conta}-{digito}"
