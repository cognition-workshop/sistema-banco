import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.generic import TemplateView
from collections import defaultdict


class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            account = demo_user.account
            
            recent_transactions = account.transactions.all().order_by('-timestamp')[:10]
            
            balance_data = self.get_balance_chart_data(account)
            
            transaction_data = self.get_transaction_distribution_data(account)
            
            context.update({
                'account': account,
                'recent_transactions': recent_transactions,
                'balance_chart_data': json.dumps(balance_data),
                'transaction_chart_data': json.dumps(transaction_data),
            })
        
        return context
    
    def get_balance_chart_data(self, account):
        transactions = account.transactions.all().order_by('timestamp')
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = transactions.filter(timestamp__gte=thirty_days_ago)
        
        labels = []
        values = []
        
        for transaction in recent_transactions:
            labels.append(transaction.timestamp.strftime('%m/%d'))
            values.append(float(transaction.balance_after_transaction))
        
        if not labels:
            labels = ['Today']
            values = [float(account.balance)]
        
        return {
            'labels': labels,
            'values': values
        }
    
    def get_transaction_distribution_data(self, account):
        from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
        
        transactions = account.transactions.all()
        
        type_counts = defaultdict(int)
        for transaction in transactions:
            type_counts[transaction.transaction_type] += 1
        
        return {
            'labels': ['Deposits', 'Withdrawals', 'Interest'],
            'values': [
                type_counts.get(DEPOSIT, 0),
                type_counts.get(WITHDRAWAL, 0),
                type_counts.get(INTEREST, 0)
            ]
        }
