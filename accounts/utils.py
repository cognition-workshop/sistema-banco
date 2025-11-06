def calculate_dac10(agency, account_number):
    """
    Calculate check digit using DAC10 (modulo 10) algorithm.
    
    Args:
        agency: 4-digit agency number (string)
        account_number: 7-digit account number (string)
    
    Returns:
        Single digit check digit (string)
    """
    combined = agency + account_number
    
    weights = [2, 1] * 6
    weights = weights[:len(combined)]
    weights.reverse()
    
    total = 0
    for i, digit in enumerate(combined):
        product = int(digit) * weights[i]
        if product > 9:
            product = sum(int(d) for d in str(product))
        total += product
    
    check_digit = (10 - (total % 10)) % 10
    
    return str(check_digit)


def validate_dac10(agency, account_number, check_digit):
    """
    Validate that the check digit is correct for given agency and account.
    
    Args:
        agency: 4-digit agency number (string)
        account_number: 7-digit account number (string)
        check_digit: 1-digit check digit (string)
    
    Returns:
        Boolean indicating if check digit is valid
    """
    expected_digit = calculate_dac10(agency, account_number)
    return check_digit == expected_digit


def format_account(agency, account_number, check_digit):
    """Format account as AAAA-CCCCCCC-D"""
    return f"{agency}-{account_number}-{check_digit}"
