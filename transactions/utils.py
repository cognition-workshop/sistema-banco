def process_account_interest(account, current_month):
    """
    Process interest calculation for a single account.
    
    Args:
        account: UserBankAccount instance
        current_month: The current month number (1-12)
    
    Returns:
        tuple: (interest_amount, new_balance) if interest was calculated
        None: if no interest should be calculated this month
    """
    if current_month not in account.get_interest_calculation_months():
        return None
    
    interest = account.account_type.calculate_interest(account.balance)
    new_balance = account.balance + interest
    
    return (interest, new_balance)
