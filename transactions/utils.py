from decimal import Decimal
from django.utils import timezone

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


def process_monthly_interest(current_time=None):
    if current_time is None:
        current_time = timezone.now()
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__isnull=False,
        initial_deposit_date__isnull=False
    ).select_related('account_type')
    
    this_month = current_time.month
    
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
        'accounts_processed': len(updated_accounts),
        'total_interest_paid': total_interest,
        'transactions_created': len(created_transactions)
    }
