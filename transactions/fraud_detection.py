from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg

from transactions.models import Transaction, FraudAlert
from transactions.constants import WITHDRAWAL


def check_multiple_transactions(account, transaction):
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    recent_count = Transaction.objects.filter(
        account=account,
        timestamp__gte=five_minutes_ago
    ).count()
    
    if recent_count >= 3:
        FraudAlert.objects.create(
            account=account,
            alert_type='MULTIPLE_TRANS',
            severity='MEDIUM',
            description=f'Account has {recent_count} transactions in the last 5 minutes',
            transaction=transaction
        )
        return True
    return False


def check_high_amount(account, transaction):
    avg_amount = Transaction.objects.filter(
        account=account,
        transaction_type=transaction.transaction_type
    ).aggregate(Avg('amount'))['amount__avg']
    
    if avg_amount and transaction.amount > avg_amount * 10:
        FraudAlert.objects.create(
            account=account,
            alert_type='HIGH_AMOUNT',
            severity='HIGH',
            description=f'Transaction amount ${transaction.amount} is 10x higher than average ${avg_amount:.2f}',
            transaction=transaction
        )
        return True
    return False


def check_rapid_withdrawals(account):
    one_hour_ago = timezone.now() - timedelta(hours=1)
    withdrawal_count = Transaction.objects.filter(
        account=account,
        transaction_type=WITHDRAWAL,
        timestamp__gte=one_hour_ago
    ).count()
    
    if withdrawal_count >= 5:
        FraudAlert.objects.create(
            account=account,
            alert_type='RAPID_WITHDRAW',
            severity='HIGH',
            description=f'Account has {withdrawal_count} withdrawals in the last hour'
        )
        return True
    return False


def run_fraud_checks(account, transaction):
    check_multiple_transactions(account, transaction)
    check_high_amount(account, transaction)
    check_rapid_withdrawals(account)
