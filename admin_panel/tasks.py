from celery import shared_task
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL
from .models import FraudAlert


@shared_task
def check_fraud_patterns():
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    
    accounts_with_multiple_withdrawals = (
        Transaction.objects
        .filter(timestamp__gte=one_hour_ago, transaction_type=WITHDRAWAL)
        .values('account')
        .annotate(withdrawal_count=Count('id'))
        .filter(withdrawal_count__gte=3)
    )
    
    for item in accounts_with_multiple_withdrawals:
        transactions = Transaction.objects.filter(
            account_id=item['account'],
            timestamp__gte=one_hour_ago,
            transaction_type=WITHDRAWAL
        )
        
        for transaction in transactions:
            if not FraudAlert.objects.filter(transaction=transaction).exists():
                FraudAlert.objects.create(
                    transaction=transaction,
                    rule_triggered='multiple_withdrawals',
                    severity='medium',
                    details=f"Account made {item['withdrawal_count']} withdrawals in 1 hour"
                )
    
    avg_amount = Transaction.objects.aggregate(avg=Avg('amount'))['avg'] or 0
    if avg_amount > 0:
        threshold = avg_amount * 10
        large_transactions = Transaction.objects.filter(
            timestamp__gte=one_hour_ago,
            amount__gte=threshold
        )
        
        for transaction in large_transactions:
            if not FraudAlert.objects.filter(transaction=transaction).exists():
                FraudAlert.objects.create(
                    transaction=transaction,
                    rule_triggered='large_amount',
                    severity='high',
                    details=f"Transaction amount ${transaction.amount} is 10x above average ${avg_amount:.2f}"
                )
    
    negative_balance_transactions = Transaction.objects.filter(
        timestamp__gte=one_hour_ago,
        balance_after_transaction__lt=0
    )
    
    for transaction in negative_balance_transactions:
        if not FraudAlert.objects.filter(transaction=transaction).exists():
            FraudAlert.objects.create(
                transaction=transaction,
                rule_triggered='negative_balance',
                severity='high',
                details=f"Transaction resulted in negative balance: ${transaction.balance_after_transaction}"
            )
    
    return f"Fraud check completed. Found {FraudAlert.objects.filter(status='pending').count()} pending alerts."
