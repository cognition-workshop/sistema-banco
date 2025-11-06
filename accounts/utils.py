from decimal import Decimal


def calculate_compound_interest(principal, annual_interest_rate, interest_calculation_per_year):
    """
    Calculate compound interest using a simplified formula.
    
    Args:
        principal (Decimal): The principal amount (account balance)
        annual_interest_rate (Decimal): Annual interest rate (0-100)
        interest_calculation_per_year (int): Number of times interest is calculated per year (1-12)
    
    Returns:
        Decimal: The calculated interest amount, rounded to 2 decimal places
    """
    p = principal
    r = annual_interest_rate
    n = Decimal(interest_calculation_per_year)
    
    interest = (p * (1 + ((r/100) / n))) - p
    
    return round(interest, 2)
