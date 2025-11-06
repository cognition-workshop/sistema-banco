from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            recent_transactions = Transaction.objects.filter(
                account=demo_user.account
            ).order_by('-timestamp')[:5]
            
            all_transactions = Transaction.objects.filter(
                account=demo_user.account
            ).order_by('-timestamp')
            
            total_deposits = sum(
                t.amount for t in all_transactions if t.transaction_type == DEPOSIT
            )
            total_withdrawals = sum(
                t.amount for t in all_transactions if t.transaction_type == WITHDRAWAL
            )
            
            context.update({
                'user': demo_user,
                'account': demo_user.account,
                'recent_transactions': recent_transactions,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'transaction_count': all_transactions.count(),
            })
        
        return context
