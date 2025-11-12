from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Transaction, FraudAlert, FraudPattern
from .constants import WITHDRAWAL
from accounts.models import UserBankAccount


class FraudDetectionService:
    
    HIGH_AMOUNT_THRESHOLD = Decimal('10000.00')
    MULTIPLE_TRANS_THRESHOLD = 5
    MULTIPLE_TRANS_WINDOW = timedelta(hours=1)
    RAPID_WITHDRAWAL_COUNT = 3
    RAPID_WITHDRAWAL_WINDOW = timedelta(minutes=10)
    UNUSUAL_HOUR_START = 0
    UNUSUAL_HOUR_END = 6
    
    @classmethod
    def check_high_amount(cls, transaction):
        if transaction.amount > cls.HIGH_AMOUNT_THRESHOLD:
            pattern, _ = FraudPattern.objects.get_or_create(
                name='Valor Anormalmente Alto',
                defaults={'description': 'Transação com valor acima de R$ 10.000'}
            )
            FraudAlert.objects.create(
                account=transaction.account,
                pattern=pattern,
                severity='HIGH',
                description=f'Transação de R$ {transaction.amount} detectada'
            )
            return True
        return False
    
    @classmethod
    def check_multiple_transactions(cls, transaction):
        time_threshold = timezone.now() - cls.MULTIPLE_TRANS_WINDOW
        recent_count = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=time_threshold
        ).count()
        
        if recent_count >= cls.MULTIPLE_TRANS_THRESHOLD:
            pattern, _ = FraudPattern.objects.get_or_create(
                name='Múltiplas Transações em Curto Período',
                defaults={'description': f'Mais de {cls.MULTIPLE_TRANS_THRESHOLD} transações em 1 hora'}
            )
            FraudAlert.objects.create(
                account=transaction.account,
                pattern=pattern,
                severity='MEDIUM',
                description=f'{recent_count} transações detectadas na última hora'
            )
            return True
        return False
    
    @classmethod
    def check_rapid_withdrawals(cls, transaction):
        if transaction.transaction_type != WITHDRAWAL:
            return False
            
        time_threshold = timezone.now() - cls.RAPID_WITHDRAWAL_WINDOW
        withdrawal_count = Transaction.objects.filter(
            account=transaction.account,
            transaction_type=WITHDRAWAL,
            timestamp__gte=time_threshold
        ).count()
        
        if withdrawal_count >= cls.RAPID_WITHDRAWAL_COUNT:
            pattern, _ = FraudPattern.objects.get_or_create(
                name='Saques Rápidos Sucessivos',
                defaults={'description': f'{cls.RAPID_WITHDRAWAL_COUNT}+ saques em 10 minutos'}
            )
            FraudAlert.objects.create(
                account=transaction.account,
                pattern=pattern,
                severity='HIGH',
                description=f'{withdrawal_count} saques detectados em 10 minutos'
            )
            return True
        return False
    
    @classmethod
    def check_unusual_hours(cls, transaction):
        hour = transaction.timestamp.hour
        if cls.UNUSUAL_HOUR_START <= hour < cls.UNUSUAL_HOUR_END:
            pattern, _ = FraudPattern.objects.get_or_create(
                name='Horário Incomum',
                defaults={'description': 'Transações entre 00h e 06h'}
            )
            FraudAlert.objects.create(
                account=transaction.account,
                pattern=pattern,
                severity='MEDIUM',
                description=f'Transação às {transaction.timestamp.strftime("%H:%M")}'
            )
            return True
        return False
    
    @classmethod
    def analyze_transaction(cls, transaction):
        alerts = []
        if cls.check_high_amount(transaction):
            alerts.append('high_amount')
        if cls.check_multiple_transactions(transaction):
            alerts.append('multiple_transactions')
        if cls.check_rapid_withdrawals(transaction):
            alerts.append('rapid_withdrawals')
        if cls.check_unusual_hours(transaction):
            alerts.append('unusual_hours')
        return alerts
