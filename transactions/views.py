from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, FormView

from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    TransferForm,
    WithdrawForm,
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

        form.account = account

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

            form.account = demo_user.account

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )

        return super().form_valid(form)


class TransferMoneyView(FormView):
    template_name = 'transactions/transaction_form.html'
    form_class = TransferForm
    title = 'Transfer Money to Another Account'
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs.update({'sender_account': demo_user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'title': self.title})
        return context

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        recipient = form.cleaned_data['recipient']

        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not (demo_user and hasattr(demo_user, 'account')):
            return super().form_valid(form)

        sender = demo_user.account

        with db_transaction.atomic():
            ids = sorted([sender.pk, recipient.pk])
            locked = (
                type(sender).objects.select_for_update()
                .filter(pk__in=ids)
                .in_bulk()
            )
            s = locked[sender.pk]
            r = locked[recipient.pk]

            if amount > s.balance:
                form.add_error('amount', 'Insufficient funds')
                return self.form_invalid(form)

            s.balance -= amount
            r.balance += amount
            s.save(update_fields=['balance'])
            r.save(update_fields=['balance'])

            Transaction.objects.create(
                account=s,
                amount=amount,
                transaction_type=WITHDRAWAL,
                balance_after_transaction=s.balance,
            )
            Transaction.objects.create(
                account=r,
                amount=amount,
                transaction_type=DEPOSIT,
                balance_after_transaction=r.balance,
            )

        messages.success(self.request, f'Successfully transferred {amount}$')
        return super().form_valid(form)
