from decimal import Decimal


def calculate_compound_interest(principal, annual_rate, calculations_per_year):
    """
    Calculate compound interest using the formula:
    interest = (p * (1 + ((r/100) / n))) - p
    
    Args:
        principal: The principal balance (Decimal)
        annual_rate: The annual interest rate as a percentage (Decimal)
        calculations_per_year: Number of times interest is calculated per year (int)
    
    Returns:
        Decimal: The calculated interest amount, rounded to 2 decimal places
    """
    p = principal
    r = annual_rate
    n = Decimal(calculations_per_year)
    
    interest = (p * (1 + ((r / 100) / n))) - p
    
    return round(interest, 2)
