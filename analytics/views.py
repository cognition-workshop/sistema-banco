from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Sum, Count
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL
from accounts.models import User
import csv
from django.http import HttpResponse


@method_decorator(staff_member_required, name='dispatch')
class AnalyticsDashboardView(TemplateView):
    template_name = 'admin/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['total_transactions'] = Transaction.objects.count()
        context['total_volume'] = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['deposit_count'] = Transaction.objects.filter(transaction_type=DEPOSIT).count()
        context['withdrawal_count'] = Transaction.objects.filter(transaction_type=WITHDRAWAL).count()
        
        return context


@staff_member_required
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Account', 'Type', 'Amount', 'Date', 'Balance After'])
    
    transactions = Transaction.objects.select_related('account').order_by('-timestamp')[:1000]
    for t in transactions:
        writer.writerow([
            t.account.account_no,
            t.get_transaction_type_display(),
            t.amount,
            t.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            t.balance_after_transaction
        ])
    
    return response
