from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            
            recent_transactions = Transaction.objects.filter(
                account=account
            ).order_by('-timestamp')[:5]
            
            thirty_days_ago = timezone.now() - timedelta(days=30)
            monthly_stats = Transaction.objects.filter(
                account=account,
                timestamp__gte=thirty_days_ago
            ).aggregate(
                total_deposits=Sum('amount', filter=Q(transaction_type=DEPOSIT)),
                total_withdrawals=Sum('amount', filter=Q(transaction_type=WITHDRAWAL)),
                transaction_count=Count('id')
            )
            
            context.update({
                'account': account,
                'recent_transactions': recent_transactions,
                'monthly_stats': monthly_stats,
            })
        
        return context
