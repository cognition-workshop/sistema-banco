from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, datetime
from accounts.models import UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from .models import AnalyticsReport
import csv
import json


class AnalyticsDashboardView(TemplateView):
    template_name = 'analytics/analytics_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).date()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        transactions = Transaction.objects.filter(
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        )
        
        total_volume = transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_count = transactions.count()
        
        deposits = transactions.filter(transaction_type=DEPOSIT)
        withdrawals = transactions.filter(transaction_type=WITHDRAWAL)
        interest = transactions.filter(transaction_type=INTEREST)
        
        deposits_total = deposits.aggregate(total=Sum('amount'))['total'] or 0
        withdrawals_total = withdrawals.aggregate(total=Sum('amount'))['total'] or 0
        
        average_transaction = total_volume / total_count if total_count > 0 else 0
        net_balance = deposits_total - withdrawals_total
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_volume': total_volume,
            'total_count': total_count,
            'deposits_count': deposits.count(),
            'deposits_total': deposits_total,
            'withdrawals_count': withdrawals.count(),
            'withdrawals_total': withdrawals_total,
            'interest_count': interest.count(),
            'interest_total': interest.aggregate(total=Sum('amount'))['total'] or 0,
            'average_transaction': average_transaction,
            'net_balance': net_balance,
        })
        
        return context


class ReportListView(ListView):
    model = AnalyticsReport
    template_name = 'analytics/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20


def export_transactions_csv(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    transactions = Transaction.objects.filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).select_related('account', 'account__user')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Data', 'Usuário', 'Conta', 'Tipo', 'Valor', 'Saldo Após'])
    
    for transaction in transactions:
        transaction_type = 'Depósito' if transaction.transaction_type == DEPOSIT else 'Saque' if transaction.transaction_type == WITHDRAWAL else 'Juros'
        writer.writerow([
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.account.user.email,
            transaction.account.account_no,
            transaction_type,
            f'R$ {transaction.amount}',
            f'R$ {transaction.balance_after_transaction}'
        ])
    
    return response
