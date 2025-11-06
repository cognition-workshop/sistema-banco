from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import FraudRule, FraudAlert
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL


class FraudDetector:
    
    def check_transaction(self, transaction):
        alerts = []
        rules = FraudRule.objects.filter(is_active=True)
        
        for rule in rules:
            if self._evaluate_rule(rule, transaction):
                alert = FraudAlert.objects.create(
                    transaction=transaction,
                    rule=rule,
                    status='PENDING'
                )
                alerts.append(alert)
        
        return alerts
    
    def _evaluate_rule(self, rule, transaction):
        if rule.rule_type == 'SUSPICIOUS_WITHDRAWAL':
            return self._check_suspicious_withdrawal(rule, transaction)
        elif rule.rule_type == 'UNUSUAL_HOURS':
            return self._check_unusual_hours(rule, transaction)
        elif rule.rule_type == 'REPEATED_TRANSACTIONS':
            return self._check_repeated_transactions(rule, transaction)
        elif rule.rule_type == 'EXCEEDS_MAX_AMOUNT':
            return self._check_exceeds_max_amount(rule, transaction)
        return False
    
    def _check_suspicious_withdrawal(self, rule, transaction):
        if transaction.transaction_type != WITHDRAWAL:
            return False
        
        threshold = rule.parameters.get('amount_threshold', 5000)
        percentage_threshold = rule.parameters.get('percentage_of_balance', 80)
        
        if transaction.amount > threshold:
            return True
        
        if transaction.account.balance > 0:
            percentage = (transaction.amount / transaction.account.balance) * 100
            if percentage >= percentage_threshold:
                return True
        
        return False
    
    def _check_unusual_hours(self, rule, transaction):
        start_hour = rule.parameters.get('start_hour', 22)
        end_hour = rule.parameters.get('end_hour', 6)
        
        hour = transaction.timestamp.hour
        
        if start_hour > end_hour:
            return hour >= start_hour or hour < end_hour
        else:
            return start_hour <= hour < end_hour
    
    def _check_repeated_transactions(self, rule, transaction):
        time_window = rule.parameters.get('time_window_minutes', 30)
        count_threshold = rule.parameters.get('count_threshold', 3)
        amount_threshold = rule.parameters.get('amount_threshold', 100)
        
        time_ago = transaction.timestamp - timedelta(minutes=time_window)
        
        similar_transactions = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=time_ago,
            timestamp__lte=transaction.timestamp,
            amount=transaction.amount
        ).count()
        
        if similar_transactions >= count_threshold and transaction.amount >= amount_threshold:
            return True
        
        return False
    
    def _check_exceeds_max_amount(self, rule, transaction):
        max_amount = rule.parameters.get('max_amount', 10000)
        time_restriction_start = rule.parameters.get('time_restriction_start', 22)
        time_restriction_end = rule.parameters.get('time_restriction_end', 6)
        
        hour = transaction.timestamp.hour
        
        is_restricted_time = False
        if time_restriction_start > time_restriction_end:
            is_restricted_time = hour >= time_restriction_start or hour < time_restriction_end
        else:
            is_restricted_time = time_restriction_start <= hour < time_restriction_end
        
        if is_restricted_time and transaction.amount > max_amount:
            return True
        
        return False
