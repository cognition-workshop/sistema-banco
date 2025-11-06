from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_monthly_interest(now=None):
    """
    Process monthly interest calculation for eligible bank accounts.
    
    This function extracts the business logic for interest calculation,
    making it testable and reusable outside of Celery tasks.
    
    Args:
        now: datetime object representing current time. Defaults to timezone.now()
    
    Returns:
        dict: {
            'accounts_processed': list of UserBankAccount objects that were updated,
            'transactions_created': list of Transaction objects that were created
        }
    """
    if now is None:
        now = timezone.now()
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__lte=now,
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    this_month = now.month
    
    created_transactions = []
    updated_accounts = []
    
    for account in accounts:
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
    
    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
    
    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
    
    return {
        'accounts_processed': updated_accounts,
        'transactions_created': created_transactions
    }
