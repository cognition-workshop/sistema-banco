from celery.decorators import task
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from transactions.models import Transaction
from .models import FraudRule, FraudAlert


@task(name="analyze_transaction_for_fraud")
def analyze_transaction_for_fraud(transaction_id):
    """
    Analyzes a transaction against all active fraud rules.
    Creates alerts for any violations detected.
    """
    try:
        transaction = Transaction.objects.select_related(
            'account', 'account__user'
        ).get(id=transaction_id)
    except Transaction.DoesNotExist:
        return {'error': 'Transaction not found'}

    active_rules = FraudRule.objects.filter(is_active=True)
    alerts_created = []

    for rule in active_rules:
        violated = False
        description = ""

        if rule.rule_type == 'high_amount':
            if rule.threshold_amount and transaction.amount >= rule.threshold_amount:
                violated = True
                description = f"Transaction amount ${transaction.amount} exceeds threshold of ${rule.threshold_amount}"

        elif rule.rule_type == 'frequency':
            if rule.time_window_minutes and rule.max_transactions:
                time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
                transaction_count = Transaction.objects.filter(
                    account=transaction.account,
                    timestamp__gte=time_threshold
                ).count()

                if transaction_count > rule.max_transactions:
                    violated = True
                    description = f"{transaction_count} transactions in {rule.time_window_minutes} minutes (max: {rule.max_transactions})"

        elif rule.rule_type == 'velocity':
            if rule.time_window_minutes and rule.threshold_amount:
                time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
                total_amount = Transaction.objects.filter(
                    account=transaction.account,
                    timestamp__gte=time_threshold
                ).aggregate(total=Sum('amount'))['total'] or 0

                if total_amount >= rule.threshold_amount:
                    violated = True
                    description = f"Total transaction volume ${total_amount} in {rule.time_window_minutes} minutes exceeds ${rule.threshold_amount}"

        elif rule.rule_type == 'unusual_time':
            transaction_hour = transaction.timestamp.hour
            if transaction_hour < 6 or transaction_hour > 22:
                violated = True
                description = f"Transaction at unusual time: {transaction.timestamp.strftime('%H:%M')}"

        if violated:
            alert = FraudAlert.objects.create(
                transaction=transaction,
                rule=rule,
                account=transaction.account,
                severity=rule.severity,
                description=description,
                status='pending'
            )
            alerts_created.append({
                'alert_id': alert.id,
                'rule': rule.name,
                'severity': rule.severity
            })

    return {
        'transaction_id': transaction_id,
        'alerts_created': len(alerts_created),
        'alerts': alerts_created
    }
