from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView, View
from datetime import timedelta
import csv
import json

from transactions.models import Transaction
from accounts.models import User, UserBankAccount


class AnalyticsDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'
    permission_required = 'transactions.view_transaction'


class TransactionVolumeDataView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'transactions.view_transaction'
    
    def get(self, request):
        days_ago = timezone.now() - timedelta(days=30)
        
        data = Transaction.objects.filter(
            timestamp__gte=days_ago
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('date')
        
        return JsonResponse({
            'labels': [item['date'].strftime('%Y-%m-%d') for item in data],
            'transaction_counts': [item['count'] for item in data],
            'transaction_amounts': [float(item['total_amount']) for item in data],
        })


class TransactionTypeDistributionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'transactions.view_transaction'
    
    def get(self, request):
        from transactions.constants import TRANSACTION_TYPE_CHOICES
        
        data = Transaction.objects.values('transaction_type').annotate(
            count=Count('id')
        )
        
        type_dict = dict(TRANSACTION_TYPE_CHOICES)
        
        return JsonResponse({
            'labels': [type_dict.get(item['transaction_type'], 'Unknown') for item in data],
            'counts': [item['count'] for item in data],
        })


class TopUsersView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'transactions.view_transaction'
    
    def get(self, request):
        top_users = Transaction.objects.values(
            'account__user__email'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')[:10]
        
        return JsonResponse({
            'labels': [item['account__user__email'] for item in top_users],
            'transaction_counts': [item['count'] for item in top_users],
            'total_amounts': [float(item['total_amount']) for item in top_users],
        })


class ExportTransactionsCSVView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'transactions.view_transaction'
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transacoes.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Data', 'Usuário', 'Email', 'Número da Conta',
            'Tipo', 'Valor', 'Saldo Após Transação'
        ])
        
        transactions = Transaction.objects.select_related(
            'account__user'
        ).all().order_by('-timestamp')[:1000]
        
        for trans in transactions:
            writer.writerow([
                trans.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                f"{trans.account.user.first_name} {trans.account.user.last_name}",
                trans.account.user.email,
                trans.account.account_no,
                trans.get_transaction_type_display(),
                trans.amount,
                trans.balance_after_transaction,
            ])
        
        return response
