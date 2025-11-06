from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
import json


class ExecutiveDashboardView(TemplateView):
    template_name = 'dashboard/executive_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_accounts = UserBankAccount.objects.count()
        total_balance = UserBankAccount.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        total_transactions = Transaction.objects.count()
        
        total_interest = Transaction.objects.filter(
            transaction_type=INTEREST
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        recent_transactions = Transaction.objects.filter(
            timestamp__gte=month_ago
        ).order_by('-timestamp')[:10]
        
        transactions_by_type = Transaction.objects.values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        daily_transactions = []
        for i in range(30):
            date = today - timedelta(days=i)
            count = Transaction.objects.filter(
                timestamp__date=date
            ).count()
            daily_transactions.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        daily_transactions.reverse()
        
        balance_evolution = []
        for i in range(30):
            date = today - timedelta(days=i)
            total = UserBankAccount.objects.filter(
                created_on__lte=date
            ).aggregate(total=Sum('balance'))['total'] or 0
            balance_evolution.append({
                'date': date.strftime('%Y-%m-%d'),
                'balance': float(total)
            })
        balance_evolution.reverse()
        
        context.update({
            'total_accounts': total_accounts,
            'total_balance': total_balance,
            'total_transactions': total_transactions,
            'total_interest': total_interest,
            'recent_transactions': recent_transactions,
            'transactions_by_type': transactions_by_type,
            'daily_transactions_json': json.dumps(daily_transactions),
            'balance_evolution_json': json.dumps(balance_evolution),
        })
        
        return context
