from decimal import Decimal
from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_interest_calculation(current_time=None):
    """
    Process interest calculation for all eligible accounts.
    
    This function handles the core business logic for calculating and applying
    interest to user bank accounts. It filters eligible accounts, calculates
    interest based on account type, updates balances, and creates transaction
    records.
    
    Args:
        current_time: Optional datetime to use for calculations. Defaults to
                     timezone.now() if not provided. Useful for testing.
        
    Returns:
        dict: Processing statistics containing:
            - accounts_processed (int): Number of accounts that had interest calculated
            - total_interest (Decimal): Total interest amount calculated
            - transactions_created (int): Number of transaction records created
    """
    if current_time is None:
        current_time = timezone.now()
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=current_time,
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    this_month = current_time.month
    
    created_transactions = []
    updated_accounts = []
    total_interest = Decimal('0.00')
    
    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(account.balance)
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
        UserBankAccount.objects.bulk_update(updated_accounts, ['balance'])
    
    return {
        'accounts_processed': len(updated_accounts),
        'total_interest': total_interest,
        'transactions_created': len(created_transactions)
    }
