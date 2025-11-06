from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum
from .models import FraudAlert
from transactions.models import Transaction
from accounts.models import UserBankAccount
import logging

logger = logging.getLogger(__name__)


class FraudDetectionService:
    VELOCITY_CHECK_MINUTES = 30
    VELOCITY_THRESHOLD = 5
    HIGH_AMOUNT_THRESHOLD = Decimal('10000.00')
    UNUSUAL_HOUR_START = 2
    UNUSUAL_HOUR_END = 5
    
    @classmethod
    def check_transaction(cls, transaction):
        alerts_created = []
        
        alert = cls.check_velocity(transaction)
        if alert:
            alerts_created.append(alert)
        
        alert = cls.check_high_amount(transaction)
        if alert:
            alerts_created.append(alert)
        
        alert = cls.check_unusual_time(transaction)
        if alert:
            alerts_created.append(alert)
        
        return alerts_created
    
    @classmethod
    def check_velocity(cls, transaction):
        time_window = timezone.now() - timedelta(minutes=cls.VELOCITY_CHECK_MINUTES)
        
        recent_transactions = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=time_window,
            transaction_type='WITHDRAWAL'
        ).count()
        
        if recent_transactions >= cls.VELOCITY_THRESHOLD:
            alert = FraudAlert.objects.create(
                account=transaction.account,
                transaction=transaction,
                alert_type='VELOCITY_CHECK',
                description=f'Múltiplos saques detectados: {recent_transactions} saques em {cls.VELOCITY_CHECK_MINUTES} minutos',
                severity=FraudAlert.SEVERITY_HIGH,
                metadata={
                    'transaction_count': recent_transactions,
                    'time_window_minutes': cls.VELOCITY_CHECK_MINUTES,
                }
            )
            logger.warning(f'Velocity check alert created for account {transaction.account.account_no}')
            return alert
        
        return None
    
    @classmethod
    def check_high_amount(cls, transaction):
        if transaction.transaction_type == 'WITHDRAWAL' and transaction.amount > cls.HIGH_AMOUNT_THRESHOLD:
            alert = FraudAlert.objects.create(
                account=transaction.account,
                transaction=transaction,
                alert_type='HIGH_AMOUNT',
                description=f'Saque de valor alto detectado: R$ {transaction.amount}',
                severity=FraudAlert.SEVERITY_CRITICAL,
                metadata={
                    'amount': str(transaction.amount),
                    'threshold': str(cls.HIGH_AMOUNT_THRESHOLD),
                }
            )
            logger.warning(f'High amount alert created for account {transaction.account.account_no}')
            return alert
        
        return None
    
    @classmethod
    def check_unusual_time(cls, transaction):
        hour = transaction.timestamp.hour
        
        if cls.UNUSUAL_HOUR_START <= hour < cls.UNUSUAL_HOUR_END:
            alert = FraudAlert.objects.create(
                account=transaction.account,
                transaction=transaction,
                alert_type='UNUSUAL_TIME',
                description=f'Transação em horário incomum: {hour}:00h',
                severity=FraudAlert.SEVERITY_MEDIUM,
                metadata={
                    'hour': hour,
                    'transaction_time': transaction.timestamp.isoformat(),
                }
            )
            logger.info(f'Unusual time alert created for account {transaction.account.account_no}')
            return alert
        
        return None
    
    @classmethod
    def get_account_risk_score(cls, account):
        recent_alerts = FraudAlert.objects.filter(
            account=account,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        risk_score = 0
        
        for alert in recent_alerts:
            if alert.severity == FraudAlert.SEVERITY_CRITICAL:
                risk_score += 10
            elif alert.severity == FraudAlert.SEVERITY_HIGH:
                risk_score += 5
            elif alert.severity == FraudAlert.SEVERITY_MEDIUM:
                risk_score += 2
            else:
                risk_score += 1
        
        return min(risk_score, 100)
