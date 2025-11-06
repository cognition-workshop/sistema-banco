from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView
from django.db.models import Sum, Count
from django.http import HttpResponse
import csv
from datetime import datetime

from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
    IRPFReportForm,
)
from transactions.models import Transaction


class TransactionRepostView(ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = TransactionDateRangeForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return super().get_queryset().none()
        
        queryset = super().get_queryset().filter(
            account=demo_user.account
        )

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context.update({
            'account': demo_user.account if demo_user and hasattr(demo_user, 'account') else None,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })

        return context


class TransactionCreateMixin(CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs.update({
                'account': demo_user.account
            })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Money to Your Account'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        if not account:
            return super().form_valid(form)

        if not account.initial_deposit_date:
            now = timezone.now()
            next_interest_month = int(
                12 / account.account_type.interest_calculation_per_year
            )
            account.initial_deposit_date = now
            account.interest_start_date = (
                now + relativedelta(
                    months=+next_interest_month
                )
            )

        account.balance += amount
        account.save(
            update_fields=[
                'initial_deposit_date',
                'balance',
                'interest_start_date'
            ]
        )

        messages.success(
            self.request,
            f'{amount}$ was deposited to your account successfully'
        )

        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            demo_user.account.balance -= form.cleaned_data.get('amount')
            demo_user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )

        return super().form_valid(form)


class IRPFReportView(ListView):
    template_name = 'transactions/irpf_report.html'
    model = Transaction
    context_object_name = 'transactions'
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return Transaction.objects.none()
        
        queryset = Transaction.objects.filter(account=demo_user.account)
        
        selected_year = self.request.GET.get('year')
        if selected_year:
            try:
                year = int(selected_year)
                queryset = queryset.filter(
                    timestamp__year=year
                )
            except (ValueError, TypeError):
                pass
        
        return queryset.order_by('timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            years = Transaction.objects.filter(
                account=demo_user.account
            ).dates('timestamp', 'year', order='DESC')
            available_years = [date.year for date in years]
        else:
            available_years = []
        
        current_year = datetime.now().year
        if current_year not in available_years:
            available_years.insert(0, current_year)
        
        selected_year = self.request.GET.get('year')
        if not selected_year and available_years:
            selected_year = str(current_year)
        
        queryset = self.get_queryset()
        summary = {
            'deposits': queryset.filter(transaction_type=DEPOSIT).aggregate(
                total=Sum('amount'),
                count=Count('id')
            ),
            'withdrawals': queryset.filter(transaction_type=WITHDRAWAL).aggregate(
                total=Sum('amount'),
                count=Count('id')
            ),
            'interest': queryset.filter(transaction_type=INTEREST).aggregate(
                total=Sum('amount'),
                count=Count('id')
            ),
        }
        
        context.update({
            'account': demo_user.account if demo_user and hasattr(demo_user, 'account') else None,
            'form': IRPFReportForm(
                self.request.GET or None,
                available_years=available_years
            ),
            'selected_year': selected_year,
            'summary': summary,
            'available_years': available_years,
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            return self.export_csv()
        return super().get(request, *args, **kwargs)
    
    def export_csv(self):
        response = HttpResponse(content_type='text/csv')
        selected_year = self.request.GET.get('year', datetime.now().year)
        response['Content-Disposition'] = f'attachment; filename="irpf_report_{selected_year}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Data', 'Tipo de Transação', 'Valor (R$)', 'Saldo Após Transação (R$)'])
        
        queryset = self.get_queryset()
        for transaction in queryset:
            writer.writerow([
                transaction.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                transaction.get_transaction_type_display(),
                f'{transaction.amount:.2f}',
                f'{transaction.balance_after_transaction:.2f}',
            ])
        
        return response
