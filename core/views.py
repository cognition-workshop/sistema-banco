from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta


class HomeView(TemplateView):
    template_name = 'core/index.html'


class DashboardView(TemplateView):
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from transactions.models import Transaction
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            transactions = Transaction.objects.filter(
                account=account,
                timestamp__gte=month_start
            )
            
            context['account'] = account
            context['balance'] = account.balance
            context['total_received'] = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
            context['total_spent'] = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0)
            context['recent_transactions'] = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]
            
            dates = []
            balances = []
            for i in range(30, -1, -1):
                date = (now - timedelta(days=i)).date()
                daily_transactions = Transaction.objects.filter(
                    account=account,
                    timestamp__date=date
                ).order_by('-timestamp').first()
                if daily_transactions:
                    dates.append(date.strftime('%d/%m'))
                    balances.append(float(daily_transactions.balance_after_transaction))
            
            if dates:
                context['dates'] = dates
                context['balances'] = balances
        
        return context
