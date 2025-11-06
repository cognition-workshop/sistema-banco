from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class DashboardView(TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            context['account'] = None
            context['stats'] = {}
            context['recent_transactions'] = []
            context['balance_chart_labels'] = json.dumps([])
            context['balance_chart_values'] = json.dumps([])
            context['monthly_chart_labels'] = json.dumps([])
            context['monthly_chart_values'] = json.dumps([])
            return context
        
        account = demo_user.account
        context['account'] = account
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=thirty_days_ago
        ).order_by('timestamp')
        
        deposit_stats = transactions.filter(transaction_type=DEPOSIT).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        withdrawal_stats = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        interest_stats = transactions.filter(transaction_type=INTEREST).aggregate(
            count=Count('id')
        )
        
        context['stats'] = {
            'deposit_count': deposit_stats['count'] or 0,
            'deposit_total': deposit_stats['total'] or 0,
            'withdrawal_count': withdrawal_stats['count'] or 0,
            'withdrawal_total': withdrawal_stats['total'] or 0,
            'interest_count': interest_stats['count'] or 0,
            'total_count': transactions.count()
        }
        
        context['recent_transactions'] = transactions.order_by('-timestamp')[:10]
        
        balance_labels = []
        balance_values = []
        for transaction in transactions:
            balance_labels.append(transaction.timestamp.strftime('%m/%d'))
            balance_values.append(float(transaction.balance_after_transaction))
        
        if not balance_labels:
            balance_labels = ['Today']
            balance_values = [float(account.balance)]
        
        context['balance_chart_labels'] = json.dumps(balance_labels)
        context['balance_chart_values'] = json.dumps(balance_values)
        
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=six_months_ago
        )
        
        monthly_data = {}
        for transaction in monthly_transactions:
            month_key = transaction.timestamp.strftime('%B')
            monthly_data[month_key] = monthly_data.get(month_key, 0) + 1
        
        if not monthly_data:
            monthly_data = {timezone.now().strftime('%B'): 0}
        
        context['monthly_chart_labels'] = json.dumps(list(monthly_data.keys()))
        context['monthly_chart_values'] = json.dumps(list(monthly_data.values()))
        
        return context
