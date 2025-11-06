import csv
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from accounts.decorators import admin_required, permission_required
from accounts.models import VIEW_REPORTS
from transactions.models import Transaction
from transactions.forms import TransactionDateRangeForm

User = get_user_model()


@method_decorator(admin_required, name='dispatch')
@method_decorator(permission_required(VIEW_REPORTS), name='dispatch')
class TransactionMonitoringView(ListView):
    model = Transaction
    template_name = 'admin/transaction_monitor.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'account__user',
            'account__account_type'
        ).all().order_by('-timestamp')
        
        form = TransactionDateRangeForm(self.request.GET or None)
        if form.is_valid():
            daterange = form.cleaned_data.get('daterange')
            if daterange:
                queryset = queryset.filter(timestamp__date__range=daterange)
        
        transaction_type = self.request.GET.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        min_amount = self.request.GET.get('min_amount')
        if min_amount:
            try:
                queryset = queryset.filter(amount__gte=float(min_amount))
            except (ValueError, TypeError):
                pass
        
        max_amount = self.request.GET.get('max_amount')
        if max_amount:
            try:
                queryset = queryset.filter(amount__lte=float(max_amount))
            except (ValueError, TypeError):
                pass
        
        user_email = self.request.GET.get('user_email')
        if user_email:
            queryset = queryset.filter(account__user__email__icontains=user_email)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TransactionDateRangeForm(self.request.GET or None)
        
        from transactions.constants import TRANSACTION_TYPE_CHOICES
        context['transaction_types'] = TRANSACTION_TYPE_CHOICES
        
        queryset = self.get_queryset()
        context['total_transactions'] = queryset.count()
        context['total_amount'] = sum(t.amount for t in queryset)
        
        return context


@admin_required
@permission_required(VIEW_REPORTS)
def export_transactions_csv(request):
    queryset = Transaction.objects.select_related(
        'account__user',
        'account__account_type'
    ).all().order_by('-timestamp')
    
    form = TransactionDateRangeForm(request.GET or None)
    if form.is_valid():
        daterange = form.cleaned_data.get('daterange')
        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)
    
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)
    
    min_amount = request.GET.get('min_amount')
    if min_amount:
        try:
            queryset = queryset.filter(amount__gte=float(min_amount))
        except (ValueError, TypeError):
            pass
    
    max_amount = request.GET.get('max_amount')
    if max_amount:
        try:
            queryset = queryset.filter(amount__lte=float(max_amount))
        except (ValueError, TypeError):
            pass
    
    user_email = request.GET.get('user_email')
    if user_email:
        queryset = queryset.filter(account__user__email__icontains=user_email)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp',
        'User Email',
        'Account Number',
        'Transaction Type',
        'Amount',
        'Balance After Transaction'
    ])
    
    for transaction in queryset:
        writer.writerow([
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.account.user.email,
            transaction.account.account_no,
            transaction.get_transaction_type_display(),
            transaction.amount,
            transaction.balance_after_transaction
        ])
    
    return response
