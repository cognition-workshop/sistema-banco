from decimal import Decimal
from typing import List, Tuple

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_for_accounts(
    accounts: List[UserBankAccount],
    current_month: int
) -> Tuple[List[Transaction], List[UserBankAccount]]:
    """
    Calculate and process interest for eligible accounts.
    
    Args:
        accounts: List of UserBankAccount objects to process
        current_month: Current month number (1-12)
        
    Returns:
        Tuple of (transactions_to_create, accounts_to_update)
    """
    created_transactions = []
    updated_accounts = []
    
    for account in accounts:
        if current_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            
            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)
    
    return created_transactions, updated_accounts
