from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            
            transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
            
            total_deposits = transactions.filter(transaction_type=DEPOSIT).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            total_withdrawals = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            account_age = 0
            if account.initial_deposit_date:
                account_age = (timezone.now().date() - account.initial_deposit_date).days
            
            recent_transactions = transactions[:5]
            
            chart_transactions = transactions.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(days=30)
            ).order_by('timestamp')
            
            context.update({
                'account': account,
                'user': demo_user,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'transaction_count': transactions.count(),
                'account_age': account_age,
                'recent_transactions': recent_transactions,
                'chart_transactions': chart_transactions,
            })
        
        return context
