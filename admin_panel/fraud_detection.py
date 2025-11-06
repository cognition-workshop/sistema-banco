from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from .models import FraudAlert
from transactions.models import Transaction


class FraudDetectionService:
    AMOUNT_THRESHOLD = Decimal('10000.00')
    FREQUENCY_LIMIT = 10
    FREQUENCY_WINDOW = 1
    VELOCITY_WINDOW = 7
    
    @classmethod
    def check_transaction(cls, transaction):
        alerts = []
        
        alert = cls._check_amount_threshold(transaction)
        if alert:
            alerts.append(alert)
        
        alert = cls._check_frequency(transaction)
        if alert:
            alerts.append(alert)
        
        alert = cls._check_velocity(transaction)
        if alert:
            alerts.append(alert)
        
        return alerts
    
    @classmethod
    def _check_amount_threshold(cls, transaction):
        if transaction.amount >= cls.AMOUNT_THRESHOLD:
            return cls.create_alert(
                user=transaction.account.user,
                transaction=transaction,
                rule_triggered='AMOUNT_THRESHOLD',
                severity='HIGH',
                description=f'Transaction amount ${transaction.amount} exceeds threshold ${cls.AMOUNT_THRESHOLD}'
            )
        return None
    
    @classmethod
    def _check_frequency(cls, transaction):
        time_threshold = timezone.now() - timedelta(hours=cls.FREQUENCY_WINDOW)
        recent_transactions = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=time_threshold
        ).count()
        
        if recent_transactions >= cls.FREQUENCY_LIMIT:
            return cls.create_alert(
                user=transaction.account.user,
                transaction=transaction,
                rule_triggered='FREQUENCY',
                severity='MEDIUM',
                description=f'{recent_transactions} transactions in {cls.FREQUENCY_WINDOW} hour(s)'
            )
        return None
    
    @classmethod
    def _check_velocity(cls, transaction):
        time_threshold = timezone.now() - timedelta(days=cls.VELOCITY_WINDOW)
        recent_transactions = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=time_threshold
        ).exclude(id=transaction.id)
        
        if recent_transactions.exists():
            avg_amount = sum(t.amount for t in recent_transactions) / recent_transactions.count()
            if transaction.amount > avg_amount * 3:
                return cls.create_alert(
                    user=transaction.account.user,
                    transaction=transaction,
                    rule_triggered='VELOCITY',
                    severity='MEDIUM',
                    description=f'Transaction amount ${transaction.amount} is 3x higher than recent average ${avg_amount:.2f}'
                )
        return None
    
    @classmethod
    def create_alert(cls, user, transaction, rule_triggered, severity, description):
        alert = FraudAlert.objects.create(
            user=user,
            transaction=transaction,
            rule_triggered=rule_triggered,
            severity=severity,
            description=description
        )
        return alert
