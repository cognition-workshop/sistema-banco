from dateutil.relativedelta import relativedelta
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError, DatabaseError
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

logger = logging.getLogger(__name__)


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
        try:
            queryset = super().get_queryset().filter(
                account=self.request.user.account
            )
        except AttributeError:
            logger.error(f'User {self.request.user.email} does not have an account')
            return Transaction.objects.none()

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })

        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs.update({
                'account': self.request.user.account
            })
        except AttributeError:
            logger.error(f'User {self.request.user.email} does not have an account')
            raise
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

    @transaction.atomic
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        try:
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

            logger.info(
                f'Deposit successful: User {self.request.user.email}, '
                f'Amount: {amount}, New Balance: {account.balance}'
            )

            messages.success(
                self.request,
                f'{amount}$ was deposited to your account successfully'
            )

            return super().form_valid(form)
        except (IntegrityError, DatabaseError) as e:
            logger.error(
                f'Deposit failed: User {self.request.user.email}, Amount: {amount}, Error: {str(e)}',
                exc_info=True
            )
            messages.error(
                self.request,
                'Erro ao processar depósito. Por favor, tente novamente ou contate o suporte.'
            )
            return self.form_invalid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    @transaction.atomic
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        try:
            if amount > account.balance:
                logger.warning(
                    f'Withdrawal attempt with insufficient balance: User {self.request.user.email}, '
                    f'Amount: {amount}, Balance: {account.balance}'
                )
                messages.error(
                    self.request,
                    f'Saldo insuficiente. Seu saldo atual é R$ {account.balance}'
                )
                return self.form_invalid(form)

            account.balance -= amount
            account.save(update_fields=['balance'])

            logger.info(
                f'Withdrawal successful: User {self.request.user.email}, '
                f'Amount: {amount}, New Balance: {account.balance}'
            )

            messages.success(
                self.request,
                f'Successfully withdrawn {amount}$ from your account'
            )

            return super().form_valid(form)
        except (IntegrityError, DatabaseError) as e:
            logger.error(
                f'Withdrawal failed: User {self.request.user.email}, Amount: {amount}, Error: {str(e)}',
                exc_info=True
            )
            messages.error(
                self.request,
                'Erro ao processar saque. Por favor, tente novamente ou contate o suporte.'
            )
            return self.form_invalid(form)
