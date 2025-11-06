import csv
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum

from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class IRPFReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/irpf_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        fiscal_year = self.request.GET.get('year')
        if fiscal_year:
            try:
                fiscal_year = int(fiscal_year)
            except ValueError:
                fiscal_year = datetime.now().year
        else:
            fiscal_year = datetime.now().year
        
        transactions = Transaction.objects.filter(
            account=self.request.user.account,
            timestamp__year=fiscal_year
        )
        
        deposits = transactions.filter(transaction_type=DEPOSIT).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        withdrawals = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        interest = transactions.filter(transaction_type=INTEREST).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        context.update({
            'fiscal_year': fiscal_year,
            'account': self.request.user.account,
            'total_deposits': deposits,
            'total_withdrawals': withdrawals,
            'total_interest': interest,
            'transactions': transactions.order_by('timestamp'),
            'available_years': self._get_available_years(),
        })
        
        return context
    
    def _get_available_years(self):
        """Get list of years with transactions"""
        years = Transaction.objects.filter(
            account=self.request.user.account
        ).dates('timestamp', 'year').values_list('timestamp__year', flat=True)
        return sorted(set(years), reverse=True)


class IRPFExportCSVView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        fiscal_year = request.GET.get('year', datetime.now().year)
        try:
            fiscal_year = int(fiscal_year)
        except ValueError:
            fiscal_year = datetime.now().year
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="irpf_{fiscal_year}_{request.user.account.account_no}.csv"'
        
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        writer.writerow([
            'Data',
            'Tipo',
            'Valor (R$)',
            'Saldo Após Transação (R$)'
        ])
        
        transactions = Transaction.objects.filter(
            account=request.user.account,
            timestamp__year=fiscal_year
        ).order_by('timestamp')
        
        for txn in transactions:
            writer.writerow([
                txn.timestamp.strftime('%d/%m/%Y %H:%M'),
                txn.get_transaction_type_display(),
                f'{txn.amount:.2f}',
                f'{txn.balance_after_transaction:.2f}'
            ])
        
        writer.writerow([])
        writer.writerow(['RESUMO ANUAL'])
        writer.writerow([])
        
        deposits = transactions.filter(transaction_type=DEPOSIT).aggregate(
            total=Sum('amount')
        )['total'] or 0
        withdrawals = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
            total=Sum('amount')
        )['total'] or 0
        interest = transactions.filter(transaction_type=INTEREST).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        writer.writerow(['Total de Depósitos', f'{deposits:.2f}'])
        writer.writerow(['Total de Saques', f'{withdrawals:.2f}'])
        writer.writerow(['Total de Juros Recebidos', f'{interest:.2f}'])
        
        return response
