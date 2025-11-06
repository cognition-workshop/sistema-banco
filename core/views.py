from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            return context
        
        account = demo_user.account
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=month_start
        )
        
        month_deposits = month_transactions.filter(
            transaction_type=DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_withdrawals = month_transactions.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        recent_transactions = Transaction.objects.filter(
            account=account
        ).order_by('-timestamp')[:10]
        
        thirty_days_ago = now - timedelta(days=30)
        chart_transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=thirty_days_ago
        ).order_by('timestamp')
        
        context.update({
            'account': account,
            'current_balance': account.balance,
            'month_deposits': month_deposits,
            'month_withdrawals': month_withdrawals,
            'total_transactions': month_transactions.count(),
            'recent_transactions': recent_transactions,
            'chart_transactions': chart_transactions,
        })
        
        return context
