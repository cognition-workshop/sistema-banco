from django.utils import timezone
import hashlib

from celery import shared_task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction
from utils.brazilian_holidays import is_business_day, next_business_day


@shared_task(name="calculate_interest")
def calculate_interest():
    today = timezone.now().date()
    
    if not is_business_day(today):
        return
    
    accounts = UserBankAccount.objects.filter(
        balance__gt=0,
        interest_start_date__gte=timezone.now(),
        initial_deposit_date__isnull=False
    ).select_related('account_type')

    this_month = timezone.now().month

    created_transactions = []
    updated_accounts = []

    for account in accounts:
        if this_month in account.get_interest_calculation_months():
            interest = account.account_type.calculate_interest(
                account.balance
            )
            account.balance += interest
            account.save()

            transaction_obj = Transaction(
                account=account,
                transaction_type=INTEREST,
                amount=interest,
                balance_after_transaction=account.balance,
                ip_address='system',
                geolocation='N/A',
                channel='system'
            )
            hash_data = f"{account.account_no}{interest}{INTEREST}system"
            transaction_obj.hash_signature = hashlib.sha256(hash_data.encode()).hexdigest()
            
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
