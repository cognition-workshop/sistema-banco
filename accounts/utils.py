def calcular_digito_verificador(agencia, conta):
    """
    Calcula o dígito verificador usando o algoritmo módulo 11.
    
    Args:
        agencia: Número da agência (string de 4 dígitos)
        conta: Número da conta sem dígito (string)
    
    Returns:
        String com o dígito verificador (0-9 ou 'X')
    """
    input_str = str(agencia) + str(conta)
    
    soma = 0
    multiplicador = 2
    
    for i in range(len(input_str) - 1, -1, -1):
        soma += multiplicador * int(input_str[i])
        multiplicador += 1
        if multiplicador > 9:
            multiplicador = 2
    
    digito = soma % 11
    if digito == 10:
        return 'X'
    
    return str(digito)
