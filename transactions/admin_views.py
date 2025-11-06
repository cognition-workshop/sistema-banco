from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.db.models import Q
from transactions.models import Transaction
from transactions.forms import TransactionDateRangeForm


@method_decorator(staff_member_required, name='dispatch')
class TransactionDashboardView(ListView):
    model = Transaction
    template_name = 'admin/transaction_dashboard.html'
    context_object_name = 'transactions'
    paginate_by = 100
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('account__user')
        
        daterange = self.request.GET.get('daterange')
        if daterange:
            try:
                dates = daterange.split(' - ')
                if len(dates) == 2:
                    qs = qs.filter(timestamp__date__range=dates)
            except:
                pass
        
        trans_type = self.request.GET.get('transaction_type')
        if trans_type:
            qs = qs.filter(transaction_type=trans_type)
        
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(account__user__email__icontains=search)
        
        return qs.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TransactionDateRangeForm(self.request.GET or None)
        return context
