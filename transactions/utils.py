from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_for_accounts(accounts, current_month):
    """
    Process interest calculation for eligible bank accounts.
    
    This function extracts the core business logic for calculating
    and applying interest to bank accounts. It determines which accounts
    should receive interest based on their calculation schedule, computes
    the interest amount, and prepares the necessary transaction and account
    update records.
    
    Args:
        accounts: QuerySet of UserBankAccount objects that are eligible
                 for interest calculation (already filtered for balance > 0,
                 interest_start_date set, initial_deposit_date set)
        current_month: Integer representing the current month (1-12)
        
    Returns:
        tuple: A tuple containing:
            - list of Transaction objects to be created
            - list of UserBankAccount objects to be updated
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
