from datetime import timedelta
from django.utils import timezone
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL
from .models import FraudAlert


def check_fraud_rules(user, transaction_type, amount):
    """
    Check basic fraud detection rules for demo purposes.
    Returns list of alerts to create (doesn't block transaction).
    """
    alerts = []
    
    if amount > 5000:
        alerts.append({
            'rule': 'large_transaction',
            'severity': 'HIGH',
            'description': f'Large transaction detected: ${amount}'
        })
    
    if transaction_type == WITHDRAWAL:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_withdrawals = Transaction.objects.filter(
            account=user.account,
            transaction_type=WITHDRAWAL,
            timestamp__gte=one_hour_ago
        ).count()
        
        if recent_withdrawals >= 2:
            alerts.append({
                'rule': 'multiple_withdrawals',
                'severity': 'MEDIUM',
                'description': f'{recent_withdrawals + 1} withdrawals in last hour'
            })
    
    last_transaction = Transaction.objects.filter(
        account=user.account
    ).order_by('-timestamp').first()
    
    if last_transaction:
        time_diff = timezone.now() - last_transaction.timestamp
        if time_diff < timedelta(minutes=2):
            alerts.append({
                'rule': 'rapid_transactions',
                'severity': 'LOW',
                'description': f'Transaction within {time_diff.seconds} seconds of previous'
            })
    
    for alert_data in alerts:
        FraudAlert.objects.create(
            user=user,
            rule_triggered=alert_data['rule'],
            severity=alert_data['severity'],
            description=alert_data['description']
        )
    
    return len(alerts) > 0
