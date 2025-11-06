from decimal import Decimal
from typing import Dict
from django.utils import timezone
from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_for_accounts(current_date=None) -> Dict:
    """
    Process interest calculation for eligible accounts.
    
    This function extracts the interest calculation logic that was previously
    embedded in the Celery task, making it more testable and reusable.
    
    Args:
        current_date: The date to use for calculations (defaults to timezone.now()).
                     Accepts a timezone-aware datetime for full testability.
    
    Returns:
        Dictionary with processing results:
        - accounts_updated: Number of accounts that received interest
        - transactions_created: Number of interest transactions created
        - total_interest: Total interest amount distributed
    """
    if current_date is None:
        current_date = timezone.now()
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=current_date,
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    this_month = current_date.month
    
    created_transactions = []
    updated_accounts = []
    total_interest = Decimal('0.00')
    
    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            total_interest += interest
            
            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)
    
    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
    
    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    return {
        'accounts_updated': len(updated_accounts),
        'transactions_created': len(created_transactions),
        'total_interest': total_interest
    }
