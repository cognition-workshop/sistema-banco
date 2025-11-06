from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from transactions.models import Transaction
from .models import FraudRule, SuspiciousTransaction


@receiver(post_save, sender=Transaction)
def check_transaction_for_fraud(sender, instance, created, **kwargs):
    if not created:
        return
    
    active_rules = FraudRule.objects.filter(is_active=True)
    violated_rules = []
    
    for rule in active_rules:
        if rule.rule_type == FraudRule.HIGH_VALUE:
            if check_high_value_rule(instance, rule):
                violated_rules.append(rule)
        
        elif rule.rule_type == FraudRule.HIGH_FREQUENCY:
            if check_high_frequency_rule(instance, rule):
                violated_rules.append(rule)
        
        elif rule.rule_type == FraudRule.UNUSUAL_HOURS:
            if check_unusual_hours_rule(instance, rule):
                violated_rules.append(rule)
        
        elif rule.rule_type == FraudRule.PATTERN_CHANGE:
            if check_pattern_change_rule(instance, rule):
                violated_rules.append(rule)
    
    if violated_rules:
        suspicious = SuspiciousTransaction.objects.create(
            transaction=instance,
            status=SuspiciousTransaction.PENDING
        )
        suspicious.fraud_rules.set(violated_rules)


def check_high_value_rule(transaction, rule):
    threshold = Decimal(str(rule.parameters.get('threshold', 10000)))
    return abs(transaction.amount) > threshold


def check_high_frequency_rule(transaction, rule):
    count_threshold = rule.parameters.get('count', 5)
    window_minutes = rule.parameters.get('window_minutes', 10)
    
    time_window = timezone.now() - timedelta(minutes=window_minutes)
    
    recent_transactions = Transaction.objects.filter(
        account=transaction.account,
        timestamp__gte=time_window
    ).count()
    
    return recent_transactions > count_threshold


def check_unusual_hours_rule(transaction, rule):
    start_hour = rule.parameters.get('start_hour', 2)
    end_hour = rule.parameters.get('end_hour', 5)
    
    transaction_hour = transaction.timestamp.hour
    
    if start_hour <= end_hour:
        return start_hour <= transaction_hour < end_hour
    else:
        return transaction_hour >= start_hour or transaction_hour < end_hour


def check_pattern_change_rule(transaction, rule):
    deviation_multiplier = Decimal(str(rule.parameters.get('deviation_multiplier', 3)))
    
    past_transactions = Transaction.objects.filter(
        account=transaction.account
    ).exclude(
        id=transaction.id
    )
    
    if past_transactions.count() < 5:
        return False
    
    avg_amount = past_transactions.aggregate(Avg('amount'))['amount__avg']
    
    if avg_amount is None or avg_amount == 0:
        return False
    
    avg_amount = Decimal(str(avg_amount))
    
    return abs(transaction.amount) > (avg_amount * deviation_multiplier)
