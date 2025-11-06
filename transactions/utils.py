from django.utils import timezone
from typing import Tuple, List

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_for_accounts(accounts_queryset) -> Tuple[List[Transaction], List[UserBankAccount]]:
    """
    Process interest calculations for eligible accounts.
    
    For each account in the queryset:
    - Check if the current month is an interest calculation month
    - Calculate interest based on account type
    - Update account balance
    - Create an interest transaction record
    
    Args:
        accounts_queryset: QuerySet of UserBankAccount objects to process
        
    Returns:
        Tuple of (created_transactions, updated_accounts)
        - created_transactions: List of Transaction objects to be bulk created
        - updated_accounts: List of UserBankAccount objects to be bulk updated
    """
    this_month = timezone.now().month
    
    created_transactions = []
    updated_accounts = []
    
    for account in accounts_queryset:
        if this_month in account.get_interest_calculation_months():
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
