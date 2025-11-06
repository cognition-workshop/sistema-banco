from django.utils import timezone

from transactions.constants import INTEREST
from transactions.models import Transaction


def process_account_interest(account, current_month):
    """
    Process interest calculation for a single account.
    
    Args:
        account: UserBankAccount instance to process
        current_month: Current month number (1-12)
        
    Returns:
        tuple: (updated_account, transaction_obj) if interest was calculated,
               (None, None) if no interest calculation was needed
    """
    if current_month not in account.get_interest_calculation_months():
        return None, None
    
    interest = account.account_type.calculate_interest(account.balance)
    account.balance += interest
    
    transaction_obj = Transaction(
        account=account,
        transaction_type=INTEREST,
        amount=interest
    )
    
    return account, transaction_obj
