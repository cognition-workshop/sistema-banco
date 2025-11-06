from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from transactions.models import Transaction
from accounts.models import User, UserBankAccount


class Analytics:
    
    def get_transaction_volume_by_type(self, start_date=None, end_date=None):
        queryset = Transaction.objects.all()
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        result = queryset.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('transaction_type')
        
        return list(result)
    
    def get_daily_trends(self, days=30):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).extra(select={'date': 'DATE(timestamp)'}).values('date').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            avg_amount=Avg('amount')
        ).order_by('date')
        
        return list(transactions)
    
    def get_user_statistics(self):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        total_accounts = UserBankAccount.objects.count()
        total_balance = UserBankAccount.objects.aggregate(total=Sum('balance'))['total'] or 0
        avg_balance = UserBankAccount.objects.aggregate(avg=Avg('balance'))['avg'] or 0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'total_accounts': total_accounts,
            'total_balance': float(total_balance),
            'average_balance': float(avg_balance),
        }
    
    def get_fraud_statistics(self):
        from .models import FraudAlert
        
        total_alerts = FraudAlert.objects.count()
        pending_alerts = FraudAlert.objects.filter(status='PENDING').count()
        reviewed_alerts = FraudAlert.objects.filter(status='REVIEWED').count()
        false_positives = FraudAlert.objects.filter(status='FALSE_POSITIVE').count()
        
        return {
            'total_alerts': total_alerts,
            'pending_alerts': pending_alerts,
            'reviewed_alerts': reviewed_alerts,
            'false_positives': false_positives,
        }
