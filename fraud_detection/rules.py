from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL


class FraudDetectionRules:
    
    MULTIPLE_TRANSACTIONS_COUNT = 5
    MULTIPLE_TRANSACTIONS_MINUTES = 10
    HIGH_VALUE_THRESHOLD = Decimal('5000.00')
    UNUSUAL_HOURS_START = 23
    UNUSUAL_HOURS_END = 6
    
    @classmethod
    def check_multiple_transactions(cls, account):
        time_threshold = timezone.now() - timedelta(minutes=cls.MULTIPLE_TRANSACTIONS_MINUTES)
        recent_count = Transaction.objects.filter(
            account=account,
            timestamp__gte=time_threshold
        ).count()
        
        return recent_count >= cls.MULTIPLE_TRANSACTIONS_COUNT
    
    @classmethod
    def check_unusual_amount(cls, account, amount):
        from django.db.models import Avg
        
        avg_amount = Transaction.objects.filter(
            account=account
        ).aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
        
        if avg_amount > 0:
            if amount > (avg_amount * 5) or amount > cls.HIGH_VALUE_THRESHOLD:
                return True
        elif amount > cls.HIGH_VALUE_THRESHOLD:
            return True
        
        return False
    
    @classmethod
    def check_unusual_hour(cls, timestamp):
        hour = timestamp.hour
        return hour >= cls.UNUSUAL_HOURS_START or hour < cls.UNUSUAL_HOURS_END
    
    @classmethod
    def analyze_transaction(cls, account, amount, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()
        
        alerts = []
        
        if cls.check_multiple_transactions(account):
            alerts.append({
                'severity': 'high',
                'type': 'multiple_transactions',
                'message': f'Múltiplas transações ({cls.MULTIPLE_TRANSACTIONS_COUNT}+) em {cls.MULTIPLE_TRANSACTIONS_MINUTES} minutos'
            })
        
        if cls.check_unusual_amount(account, amount):
            alerts.append({
                'severity': 'medium',
                'type': 'unusual_amount',
                'message': f'Valor atípico: R$ {amount}'
            })
        
        if cls.check_unusual_hour(timestamp):
            alerts.append({
                'severity': 'low',
                'type': 'unusual_hour',
                'message': f'Transação em horário incomum: {timestamp.strftime("%H:%M")}'
            })
        
        return alerts
