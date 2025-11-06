import csv
from datetime import datetime, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, Avg, Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    
    def test_func(self):
        return self.request.user.is_staff


class AnalyticsDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from and date_to:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_from = timezone.now().date() - timedelta(days=30)
                date_to = timezone.now().date()
        else:
            date_from = timezone.now().date() - timedelta(days=30)
            date_to = timezone.now().date()
        
        context['total_users'] = User.objects.count()
        context['total_accounts'] = UserBankAccount.objects.count()
        context['total_balance'] = UserBankAccount.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        context['average_balance'] = UserBankAccount.objects.aggregate(
            avg=Avg('balance')
        )['avg'] or 0
        
        transactions_qs = Transaction.objects.filter(
            timestamp__date__gte=date_from,
            timestamp__date__lte=date_to
        )
        
        context['total_deposits'] = transactions_qs.filter(
            transaction_type=DEPOSIT
        ).count()
        context['total_withdrawals'] = transactions_qs.filter(
            transaction_type=WITHDRAWAL
        ).count()
        context['total_interest'] = transactions_qs.filter(
            transaction_type=INTEREST
        ).count()
        
        context['deposit_amount'] = transactions_qs.filter(
            transaction_type=DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['withdrawal_amount'] = transactions_qs.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['interest_amount'] = transactions_qs.filter(
            transaction_type=INTEREST
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_transactions = []
        current_date = date_from
        while current_date <= date_to:
            day_count = transactions_qs.filter(
                timestamp__date=current_date
            ).count()
            daily_transactions.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': day_count
            })
            current_date += timedelta(days=1)
        
        context['daily_transactions'] = daily_transactions
        
        context['top_accounts'] = UserBankAccount.objects.select_related(
            'user'
        ).order_by('-balance')[:10]
        
        context['date_from'] = date_from
        context['date_to'] = date_to
        
        return context


class ExportTransactionsCSVView(StaffRequiredMixin, View):
    
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Account Number',
            'User Email',
            'Transaction Type',
            'Amount',
            'Balance After Transaction',
            'Timestamp'
        ])
        
        transactions = Transaction.objects.select_related(
            'account__user'
        ).order_by('-timestamp')
        
        for transaction in transactions:
            writer.writerow([
                transaction.account.account_no,
                transaction.account.user.email,
                transaction.get_transaction_type_display(),
                transaction.amount,
                transaction.balance_after_transaction,
                transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
