from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL
from accounts.models import UserBankAccount
from core.models import FraudAlert


class FraudDetector:
    
    MULTIPLE_TRANSACTION_COUNT = 5
    MULTIPLE_TRANSACTION_WINDOW = 15
    LARGE_WITHDRAWAL_THRESHOLD = 5000
    ABNORMAL_PATTERN_MULTIPLIER = 3
    
    @classmethod
    def check_multiple_transactions(cls, account):
        time_threshold = timezone.now() - timedelta(minutes=cls.MULTIPLE_TRANSACTION_WINDOW)
        recent_transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=time_threshold
        ).count()
        
        if recent_transactions >= cls.MULTIPLE_TRANSACTION_COUNT:
            alert = FraudAlert.objects.create(
                alert_type='MULTIPLE_TRANSACTIONS',
                account=account,
                description=f'{recent_transactions} transactions in {cls.MULTIPLE_TRANSACTION_WINDOW} minutes',
                severity='MEDIUM'
            )
            return alert
        return None
    
    @classmethod
    def check_large_withdrawal(cls, transaction):
        if transaction.transaction_type == WITHDRAWAL and transaction.amount > cls.LARGE_WITHDRAWAL_THRESHOLD:
            alert = FraudAlert.objects.create(
                alert_type='LARGE_WITHDRAWAL',
                account=transaction.account,
                transaction=transaction,
                description=f'Withdrawal of ${transaction.amount:,.2f} exceeds threshold of ${cls.LARGE_WITHDRAWAL_THRESHOLD:,.2f}',
                severity='HIGH'
            )
            return alert
        return None
    
    @classmethod
    def check_abnormal_pattern(cls, transaction):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        avg_data = Transaction.objects.filter(
            account=transaction.account,
            timestamp__gte=thirty_days_ago,
            transaction_type=transaction.transaction_type
        ).exclude(id=transaction.id).aggregate(
            avg=Avg('amount')
        )
        avg_amount = avg_data['avg']
        
        if avg_amount and transaction.amount > (avg_amount * cls.ABNORMAL_PATTERN_MULTIPLIER):
            alert = FraudAlert.objects.create(
                alert_type='ABNORMAL_PATTERN',
                account=transaction.account,
                transaction=transaction,
                description=f'Transaction amount ${transaction.amount:,.2f} is {cls.ABNORMAL_PATTERN_MULTIPLIER}x average (${avg_amount:,.2f})',
                severity='MEDIUM'
            )
            return alert
        return None
    
    @classmethod
    def run_all_checks(cls, transaction):
        alerts = []
        
        alert = cls.check_multiple_transactions(transaction.account)
        if alert:
            alerts.append(alert)
        
        alert = cls.check_large_withdrawal(transaction)
        if alert:
            alerts.append(alert)
        
        alert = cls.check_abnormal_pattern(transaction)
        if alert:
            alerts.append(alert)
        
        return alerts
