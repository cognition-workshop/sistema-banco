from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class HomeView(TemplateView):
    template_name = 'core/index.html'


class UserDashboardView(TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                account=account,
                timestamp__gte=thirty_days_ago
            ).order_by('-timestamp')
            
            deposits_30d = recent_transactions.filter(transaction_type=DEPOSIT).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            withdrawals_30d = recent_transactions.filter(transaction_type=WITHDRAWAL).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            last_transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:10]
            
            balance_history = []
            for transaction in Transaction.objects.filter(
                account=account,
                timestamp__gte=thirty_days_ago
            ).order_by('timestamp'):
                balance_history.append({
                    'date': transaction.timestamp.strftime('%Y-%m-%d'),
                    'balance': float(transaction.balance_after_transaction)
                })
            
            context.update({
                'user': demo_user,
                'account': account,
                'current_balance': account.balance,
                'deposits_30d': deposits_30d,
                'withdrawals_30d': withdrawals_30d,
                'transaction_count_30d': recent_transactions.count(),
                'last_transactions': last_transactions,
                'balance_history': balance_history,
            })
        
        return context
