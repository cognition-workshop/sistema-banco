from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


class HomeView(TemplateView):
    template_name = "core/index.html"


class DashboardView(TemplateView):
    template_name = "core/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            context['account'] = None
            return context
            
        account = demo_user.account
        context['account'] = account
        
        recent_transactions = Transaction.objects.filter(
            account=account
        ).order_by('-timestamp')[:10]
        context['recent_transactions'] = recent_transactions
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        monthly_deposits = Transaction.objects.filter(
            account=account,
            transaction_type=DEPOSIT,
            timestamp__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_withdrawals = Transaction.objects.filter(
            account=account,
            transaction_type=WITHDRAWAL,
            timestamp__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['monthly_deposits'] = monthly_deposits
        context['monthly_withdrawals'] = monthly_withdrawals
        context['monthly_net'] = monthly_deposits - monthly_withdrawals
        
        six_months_ago = timezone.now() - timedelta(days=180)
        transactions = Transaction.objects.filter(
            account=account,
            timestamp__gte=six_months_ago
        ).order_by('timestamp')
        
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction.timestamp.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'deposits': 0, 'withdrawals': 0}
            
            if transaction.transaction_type == DEPOSIT:
                monthly_data[month_key]['deposits'] += float(transaction.amount)
            else:
                monthly_data[month_key]['withdrawals'] += float(transaction.amount)
        
        context['chart_months'] = list(monthly_data.keys())
        context['chart_deposits'] = [monthly_data[m]['deposits'] for m in monthly_data.keys()]
        context['chart_withdrawals'] = [monthly_data[m]['withdrawals'] for m in monthly_data.keys()]
        
        return context
