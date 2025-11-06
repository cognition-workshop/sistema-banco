from transactions.constants import INTEREST
from transactions.models import Transaction


def process_account_interest(account, current_month):
    """
    Process interest calculation for a single account.
    
    This function checks if the current month is in the account's interest
    calculation months, and if so, calculates interest, updates the account
    balance, and creates a transaction record.
    
    Args:
        account: UserBankAccount instance to process
        current_month: Integer representing the current month (1-12)
    
    Returns:
        tuple: (transaction_obj, updated_account) if interest was processed,
               (None, None) if the month is not in calculation months
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
    
    return transaction_obj, account
