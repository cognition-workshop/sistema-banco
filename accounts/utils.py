from decimal import Decimal
from django.utils import timezone
from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_calculation(accounts_queryset=None):
    """
    Calculate and apply interest to eligible bank accounts.
    
    This function handles the complete interest calculation workflow:
    - Queries eligible accounts (or uses provided queryset)
    - Checks if interest should be calculated for the current month
    - Calculates interest using account type's interest rate
    - Updates account balances
    - Creates transaction records
    
    Args:
        accounts_queryset: Optional queryset of UserBankAccount objects to process.
                          If None, will query all eligible accounts automatically.
    
    Returns:
        dict: Statistics about the operation with keys:
              - 'accounts_processed': Number of accounts that received interest
              - 'total_interest': Total interest amount calculated
              - 'transactions_created': Number of transaction records created
    """
    if accounts_queryset is None:
        accounts_queryset = UserBankAccount.objects.filter(
            balance__gt=0,
            interest_start_date__gte=timezone.now(),
            initial_deposit_date__isnull=False
        ).select_related('account_type')
    
    this_month = timezone.now().month
    
    created_transactions = []
    updated_accounts = []
    total_interest = Decimal('0')
    
    for account in accounts_queryset:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            total_interest += interest
            
            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest
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
        'accounts_processed': len(updated_accounts),
        'total_interest': total_interest,
        'transactions_created': len(created_transactions)
    }
