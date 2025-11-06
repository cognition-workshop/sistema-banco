from dateutil.relativedelta import relativedelta
from datetime import timedelta

from django.contrib import messages
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, View

from import_export import resources, fields

from accounts.models import UserBankAccount
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
    IRPFYearForm,
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


class IRPFReportView(ListView):
    template_name = 'transactions/irpf_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = IRPFYearForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return super().get_queryset().none()
        
        queryset = super().get_queryset().filter(
            account=demo_user.account
        )

        year = self.form_data.get("year")

        if year:
            queryset = queryset.filter(timestamp__year=year)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        
        transactions = self.get_queryset()
        interest_income = transactions.filter(transaction_type=INTEREST).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_deposits = transactions.filter(transaction_type=DEPOSIT).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_withdrawals = transactions.filter(transaction_type=WITHDRAWAL).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        context.update({
            'account': account,
            'form': IRPFYearForm(self.request.GET or None),
            'interest_income': interest_income,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
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
                'account': demo_user.account,
                'request': self.request
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

class AnalyticsView(ListView):
    template_name = 'transactions/analytics.html'
    model = Transaction
    context_object_name = 'transactions'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        transaction_stats = Transaction.objects.aggregate(
            total_transactions=Count('id'),
            total_volume=Sum('amount'),
            deposit_count=Count('id', filter=Q(transaction_type=DEPOSIT)),
            deposit_volume=Sum('amount', filter=Q(transaction_type=DEPOSIT)),
            withdrawal_count=Count('id', filter=Q(transaction_type=WITHDRAWAL)),
            withdrawal_volume=Sum('amount', filter=Q(transaction_type=WITHDRAWAL)),
            interest_count=Count('id', filter=Q(transaction_type=INTEREST)),
            interest_volume=Sum('amount', filter=Q(transaction_type=INTEREST)),
        )
        
        balance_stats = UserBankAccount.objects.aggregate(
            total_balance=Sum('balance'),
            account_count=Count('id')
        )
        
        User = get_user_model()
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        daily_user_growth = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('date_joined')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        monthly_user_growth = User.objects.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        daily_transactions = Transaction.objects.filter(
            timestamp__gte=thirty_days_ago
        ).annotate(
            day=TruncDate('timestamp')
        ).values('day').annotate(
            count=Count('id'),
            volume=Sum('amount')
        ).order_by('day')
        
        transactions_by_type = Transaction.objects.filter(
            timestamp__gte=thirty_days_ago
        ).values('transaction_type').annotate(
            day=TruncDate('timestamp'),
            count=Count('id'),
            volume=Sum('amount')
        ).order_by('day', 'transaction_type')
        
        context.update({
            'transaction_stats': transaction_stats,
            'balance_stats': balance_stats,
            'daily_user_growth': list(daily_user_growth),
            'monthly_user_growth': list(monthly_user_growth),
            'daily_transactions': list(daily_transactions),
            'transactions_by_type': list(transactions_by_type),
        })
        
        return context


class TransactionResource(resources.ModelResource):
    account_number = fields.Field(attribute='account__account_no', column_name='Account Number')
    user_email = fields.Field(attribute='account__user__email', column_name='User Email')
    transaction_type_display = fields.Field(attribute='get_transaction_type_display', column_name='Transaction Type')
    
    class Meta:
        model = Transaction
        fields = ('id', 'account_number', 'user_email', 'amount', 
                 'balance_after_transaction', 'transaction_type_display', 'timestamp')
        export_order = fields


class TransactionExportView(View):
    def get(self, request, *args, **kwargs):
        file_format = request.GET.get('format', 'csv')
        
        queryset = Transaction.objects.all().select_related('account__user')
        
        daterange = request.GET.get('daterange')
        if daterange:
            try:
                dates = daterange.split(' - ')
                if len(dates) == 2:
                    queryset = queryset.filter(timestamp__date__range=dates)
            except ValueError:
                pass
        
        resource = TransactionResource()
        dataset = resource.export(queryset)
        
        if file_format == 'csv':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        elif file_format == 'xlsx':
            response = HttpResponse(
                dataset.xlsx,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
        else:
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        return response
