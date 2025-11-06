from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.db.models import Sum
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from datetime import datetime, timedelta


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
            
            context['recent_transactions'] = transactions[:5]
            
            context['account'] = account
            
            total_deposits = transactions.filter(transaction_type=DEPOSIT).aggregate(Sum('amount'))['amount__sum'] or 0
            total_withdrawals = transactions.filter(transaction_type=WITHDRAWAL).aggregate(Sum('amount'))['amount__sum'] or 0
            
            context['total_deposits'] = total_deposits
            context['total_withdrawals'] = total_withdrawals
            context['transaction_count'] = transactions.count()
            
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_txns = transactions.filter(timestamp__gte=thirty_days_ago).order_by('timestamp')
            
            balance_dates = []
            balance_amounts = []
            for txn in recent_txns:
                balance_dates.append(txn.timestamp.strftime('%Y-%m-%d'))
                balance_amounts.append(float(txn.balance_after_transaction))
            
            context['balance_dates'] = balance_dates
            context['balance_amounts'] = balance_amounts
            
            context['deposit_count'] = transactions.filter(transaction_type=DEPOSIT).count()
            context['withdrawal_count'] = transactions.filter(transaction_type=WITHDRAWAL).count()
        
        return context
