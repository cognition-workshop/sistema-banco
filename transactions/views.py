import logging
from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView

from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
)
from transactions.models import Transaction

logger = logging.getLogger('security')


class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = TransactionDateRangeForm(request.GET or None)
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'account'):
            return super().get_queryset().none()
        
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user.account if hasattr(self.request.user, 'account') else None
        
        if account:
            transactions = self.get_queryset()
            
            deposits = transactions.filter(transaction_type=DEPOSIT)
            withdrawals = transactions.filter(transaction_type=WITHDRAWAL)
            
            total_deposits = sum(t.amount for t in deposits)
            total_withdrawals = sum(t.amount for t in withdrawals)
            
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_transactions = transactions.filter(timestamp__gte=thirty_days_ago).order_by('timestamp')
            
            chart_labels = []
            chart_deposits = []
            chart_withdrawals = []
            
            from collections import defaultdict
            daily_data = defaultdict(lambda: {'deposits': 0, 'withdrawals': 0})
            
            for trans in recent_transactions:
                date_str = trans.timestamp.strftime('%Y-%m-%d')
                if trans.transaction_type == DEPOSIT:
                    daily_data[date_str]['deposits'] += float(trans.amount)
                elif trans.transaction_type == WITHDRAWAL:
                    daily_data[date_str]['withdrawals'] += float(trans.amount)
            
            for date in sorted(daily_data.keys()):
                chart_labels.append(date)
                chart_deposits.append(daily_data[date]['deposits'])
                chart_withdrawals.append(daily_data[date]['withdrawals'])
        else:
            total_deposits = total_withdrawals = 0
            chart_labels = chart_deposits = chart_withdrawals = []
        
        context.update({
            'account': account,
            'form': TransactionDateRangeForm(self.request.GET or None),
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'chart_labels': chart_labels,
            'chart_deposits': chart_deposits,
            'chart_withdrawals': chart_withdrawals,
        })

        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'account'):
            kwargs.update({
                'account': self.request.user.account
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
        account = self.request.user.account

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
        
        logger.info(f'Deposit: User {self.request.user.email} deposited {amount}$')
        
        response = super().form_valid(form)
        
        from transactions.fraud_detection import run_fraud_checks
        run_fraud_checks(account, self.object)
        
        return response


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        self.request.user.account.balance -= amount
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )
        
        logger.info(f'Withdrawal: User {self.request.user.email} withdrew {amount}$')
        
        response = super().form_valid(form)
        
        from transactions.fraud_detection import run_fraud_checks
        run_fraud_checks(self.request.user.account, self.object)
        
        return response


class FraudDashboardView(LoginRequiredMixin, ListView):
    template_name = 'transactions/fraud_dashboard.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        from transactions.models import FraudAlert
        if self.request.user.is_staff:
            return FraudAlert.objects.select_related('account', 'transaction').all()
        elif hasattr(self.request.user, 'account'):
            return FraudAlert.objects.filter(account=self.request.user.account)
        return FraudAlert.objects.none()
    
    def get_context_data(self, **kwargs):
        from transactions.models import FraudAlert
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['total_alerts'] = queryset.count()
        context['unresolved_alerts'] = queryset.filter(is_resolved=False).count()
        context['high_severity'] = queryset.filter(severity='HIGH', is_resolved=False).count()
        return context
