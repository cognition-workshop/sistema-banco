"""
Utility functions for transaction processing.
"""


def process_interest_for_accounts(accounts, current_month):
    """
    Process interest calculation for a list of accounts.
    
    Args:
        accounts: QuerySet or list of UserBankAccount objects
        current_month: Integer representing the current month (1-12)
    
    Returns:
        List of tuples (account, interest_amount) for accounts that should
        receive interest in the given month
    """
    eligible_accounts = []
    
    for account in accounts:
        if current_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(account.balance)
            eligible_accounts.append((account, interest))
    
    return eligible_accounts
