from transactions.constants import INTEREST
from transactions.models import Transaction


def process_account_interest(account, current_month):
    """
    Process interest calculation for a single account.
    
    Checks if interest should be calculated for the current month,
    calculates the interest amount, updates the account balance,
    and creates a transaction record.
    
    Args:
        account: UserBankAccount instance to process
        current_month: Integer representing the current month (1-12)
    
    Returns:
        tuple: (updated_account, transaction_obj) if interest was calculated,
               (None, None) otherwise
    """
    if current_month not in account.get_interest_calculation_months():
        return None, None
    
    interest = account.account_type.calculate_interest(account.balance)
    account.balance += interest
    
    transaction_obj = Transaction(
        account=account,
        transaction_type=INTEREST,
        amount=interest,
        balance_after_transaction=account.balance
    )
    
    return account, transaction_obj
