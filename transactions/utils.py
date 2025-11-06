from decimal import Decimal


def process_account_interest(account, current_month):
    """
    Calculate interest for a bank account if applicable for the current month.
    
    Args:
        account (UserBankAccount): The bank account to process
        current_month (int): The current month number (1-12)
    
    Returns:
        dict: A dictionary with:
            - 'should_calculate' (bool): Whether interest should be calculated
            - 'interest_amount' (Decimal): The calculated interest amount (0 if not applicable)
    """
    interest_months = account.get_interest_calculation_months()
    
    if current_month not in interest_months:
        return {
            'should_calculate': False,
            'interest_amount': Decimal('0.00')
        }
    
    interest = account.account_type.calculate_interest(account.balance)
    
    return {
        'should_calculate': True,
        'interest_amount': interest
    }
