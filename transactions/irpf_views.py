import csv
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum

from .models import Transaction
from .constants import INTEREST


class IRPFReportView(TemplateView):
    """Annual IRPF (Income Tax) report"""
    template_name = 'transactions/irpf_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year', datetime.now().year)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            context.update({
                'account': None,
                'year': year,
                'total_interest': Decimal('0.00'),
                'monthly_interest': []
            })
            return context
        
        account = demo_user.account
        
        interest_transactions = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST,
            timestamp__year=year
        ).order_by('timestamp')
        
        total_interest = interest_transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        monthly_interest = []
        for month in range(1, 13):
            month_total = interest_transactions.filter(
                timestamp__month=month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            monthly_interest.append({
                'month': month,
                'month_name': datetime(year, month, 1).strftime('%B'),
                'amount': month_total
            })
        
        context.update({
            'account': account,
            'year': year,
            'total_interest': total_interest,
            'monthly_interest': monthly_interest,
            'transactions': interest_transactions
        })
        
        return context


class IRPFReportCSVView(IRPFReportView):
    """Export IRPF report as CSV"""
    
    def render_to_response(self, context, **response_kwargs):
        year = self.kwargs.get('year', datetime.now().year)
        account = context['account']
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="irpf_report_{year}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Informe de Rendimentos - Imposto de Renda'])
        writer.writerow([''])
        writer.writerow(['Ano', year])
        writer.writerow(['Titular', account.user.get_full_name()])
        writer.writerow(['CPF', account.cpf])
        writer.writerow(['Agência', account.agency])
        writer.writerow(['Conta', f'{account.account_number}-{account.account_digit}'])
        writer.writerow([''])
        writer.writerow(['Rendimentos Tributáveis (Juros)'])
        writer.writerow(['Mês', 'Valor (R$)'])
        
        for month_data in context['monthly_interest']:
            writer.writerow([
                month_data['month_name'],
                f"{month_data['amount']:.2f}"
            ])
        
        writer.writerow([''])
        writer.writerow(['Total Anual', f"{context['total_interest']:.2f}"])
        
        return response
