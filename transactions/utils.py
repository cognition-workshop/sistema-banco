from decimal import Decimal
from typing import Optional

from accounts.models import UserBankAccount


def calculate_account_interest(
    account: UserBankAccount, 
    current_month: int
) -> Optional[Decimal]:
    """
    Calculate interest for a single account if applicable for the current month.
    
    This function determines whether interest should be calculated based on the
    account's interest calculation schedule and the current month. If interest
    should be calculated, it uses the account type's interest rate to compute
    the amount.
    
    Args:
        account: The UserBankAccount to calculate interest for
        current_month: The current month (1-12)
    
    Returns:
        The interest amount as a Decimal if interest should be calculated,
        None otherwise
    """
    if current_month not in account.get_interest_calculation_months():
        return None
    
    return account.account_type.calculate_interest(account.balance)
