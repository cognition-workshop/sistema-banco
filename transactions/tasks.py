from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from celery.decorators import task

from accounts.models import UserBankAccount
from transactions.constants import INTEREST
from transactions.models import Transaction


@task(name="calculate_interest")
def calculate_interest():
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
                amount=interest
            )
            created_transactions.append(transaction_obj)
            updated_accounts.append(account)

    if created_transactions:
        Transaction.objects.bulk_create(created_transactions)
        
        from audit.models import AuditLog
        transaction_ct = ContentType.objects.get_for_model(Transaction)
        
        for transaction in created_transactions:
            new_value = {
                'id': transaction.id,
                'account_id': transaction.account_id,
                'amount': str(transaction.amount),
                'balance_after_transaction': str(transaction.balance_after_transaction),
                'transaction_type': transaction.transaction_type,
                'timestamp': transaction.timestamp.isoformat() if transaction.timestamp else None,
            }
            
            AuditLog.objects.create(
                user=None,
                action=AuditLog.ACTION_CREATE,
                content_type=transaction_ct,
                object_id=transaction.id,
                old_value=None,
                new_value=new_value,
                ip_address='0.0.0.0',
            )

    if updated_accounts:
        UserBankAccount.objects.bulk_update(
            updated_accounts, ['balance']
        )
        
        from audit.models import AuditLog
        account_ct = ContentType.objects.get_for_model(UserBankAccount)
        
        for account in updated_accounts:
            new_value = {
                'id': account.id,
                'user_id': account.user_id,
                'account_type_id': account.account_type_id,
                'account_no': account.account_no,
                'balance': str(account.balance),
                'gender': account.gender,
                'birth_date': account.birth_date.isoformat() if account.birth_date else None,
                'interest_start_date': account.interest_start_date.isoformat() if account.interest_start_date else None,
                'initial_deposit_date': account.initial_deposit_date.isoformat() if account.initial_deposit_date else None,
            }
            
            AuditLog.objects.create(
                user=None,
                action=AuditLog.ACTION_UPDATE,
                content_type=account_ct,
                object_id=account.id,
                old_value=None,
                new_value=new_value,
                ip_address='0.0.0.0',
            )
