"""
Utility functions for transaction processing.

This module contains pure functions for processing banking transactions,
particularly interest calculations, to improve testability and reusability.
"""
from decimal import Decimal
from typing import List, Tuple, Dict, Any


def process_interest_for_accounts(
    accounts: List[Any], 
    current_month: int
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process interest calculation for a list of bank accounts.
    
    This is a pure function that calculates interest for eligible accounts
    and returns the data needed to create transactions and update accounts.
    It does not perform any database operations, making it easy to test
    and reuse in different contexts.
    
    Args:
        accounts: List of UserBankAccount objects with account_type relationship loaded.
                 Each account must have: balance, account_type, and 
                 get_interest_calculation_months() method.
        current_month: Integer representing the current month (1-12).
    
    Returns:
        Tuple containing two lists:
        - First list: Dictionaries with transaction data containing keys:
            * account: The account object
            * transaction_type: Transaction type constant (INTEREST)
            * amount: Interest amount calculated
            * balance_after_transaction: New balance after interest
        - Second list: Dictionaries with account update data containing keys:
            * account: The account object to update
            * new_balance: The new balance value
    
    Raises:
        ValueError: If current_month is not between 1 and 12.
        AttributeError: If accounts don't have required attributes
                       (balance, account_type, get_interest_calculation_months).
    
    Examples:
        >>> mock_account = Mock()
        >>> mock_account.balance = Decimal('1000.00')
        >>> mock_account.account_type.calculate_interest.return_value = Decimal('10.00')
        >>> mock_account.get_interest_calculation_months.return_value = [6]
        >>> transactions, updates = process_interest_for_accounts([mock_account], 6)
        >>> len(transactions)
        1
        >>> transactions[0]['amount']
        Decimal('10.00')
        >>> transactions[0]['balance_after_transaction']
        Decimal('1010.00')
    """
    if not 1 <= current_month <= 12:
        raise ValueError(
            f"current_month must be between 1 and 12, got {current_month}"
        )
    
    transaction_data = []
    account_updates = []
    
    for account in accounts:
        if current_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(account.balance)
            
            new_balance = account.balance + interest
            
            transaction_data.append({
                'account': account,
                'transaction_type': 3,
                'amount': interest,
                'balance_after_transaction': new_balance
            })
            
            account_updates.append({
                'account': account,
                'new_balance': new_balance
            })
    
    return transaction_data, account_updates
