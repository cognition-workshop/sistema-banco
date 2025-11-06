from dateutil.relativedelta import relativedelta
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView
from django.db import transaction as db_transaction

from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
)
from transactions.models import Transaction

logger = logging.getLogger("transactions")


class TransactionRepostView(ListView):
    template_name = "transactions/transaction_report.html"
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
        demo_user = User.objects.filter(email="demo@example.com").first()
        if not demo_user or not hasattr(demo_user, "account"):
            return super().get_queryset().none()

        queryset = super().get_queryset().filter(account=demo_user.account)

        daterange = self.form_data.get("daterange")

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email="demo@example.com").first()
        context.update(
            {
                "account": (
                    demo_user.account
                    if demo_user and hasattr(demo_user, "account")
                    else None
                ),
                "form": TransactionDateRangeForm(self.request.GET or None),
            }
        )

        return context


class TransactionCreateMixin(CreateView):
    template_name = "transactions/transaction_form.html"
    model = Transaction
    title = ""
    success_url = reverse_lazy("transactions:transaction_report")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Bypass login - use demo user
        User = get_user_model()
        demo_user = User.objects.filter(email="demo@example.com").first()
        if demo_user and hasattr(demo_user, "account"):
            kwargs.update({"account": demo_user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title})

        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = "Deposit Money to Your Account"

    def get_initial(self):
        initial = {"transaction_type": DEPOSIT}
        return initial

    def form_valid(self, form):
        try:
            amount = form.cleaned_data.get("amount")
            User = get_user_model()
            demo_user = User.objects.filter(email="demo@example.com").first()
            account = (
                demo_user.account
                if demo_user and hasattr(demo_user, "account")
                else None
            )

            if not account:
                logger.error("Conta não encontrada para depósito")
                messages.error(
                    self.request, "Erro ao processar depósito. Conta não encontrada."
                )
                return super().form_valid(form)

            with db_transaction.atomic():
                if not account.initial_deposit_date:
                    now = timezone.now()
                    next_interest_month = int(
                        12 / account.account_type.interest_calculation_per_year
                    )
                    account.initial_deposit_date = now
                    account.interest_start_date = now + relativedelta(
                        months=+next_interest_month
                    )

                account.balance += amount
                account.save(
                    update_fields=[
                        "initial_deposit_date",
                        "balance",
                        "interest_start_date",
                    ]
                )

            logger.info(
                f"Depósito de {amount}$ realizado com sucesso para conta {account.account_no}"
            )
            messages.success(
                self.request, f"{amount}$ foi depositado em sua conta com sucesso"
            )
        except Exception as e:
            logger.error(f"Erro ao processar depósito: {str(e)}", exc_info=True)
            messages.error(
                self.request, "Erro ao processar depósito. Por favor, tente novamente."
            )
            return self.form_invalid(form)

        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = "Withdraw Money from Your Account"

    def get_initial(self):
        initial = {"transaction_type": WITHDRAWAL}
        return initial

    def form_valid(self, form):
        try:
            amount = form.cleaned_data.get("amount")
            User = get_user_model()
            demo_user = User.objects.filter(email="demo@example.com").first()

            if demo_user and hasattr(demo_user, "account"):
                with db_transaction.atomic():
                    demo_user.account.balance -= amount
                    demo_user.account.save(update_fields=["balance"])

                logger.info(
                    f"Saque de {amount}$ realizado com sucesso da conta {demo_user.account.account_no}"
                )
                messages.success(
                    self.request, f"Saque de {amount}$ realizado com sucesso"
                )
            else:
                logger.error("Conta não encontrada para saque")
                messages.error(
                    self.request, "Erro ao processar saque. Conta não encontrada."
                )
                return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Erro ao processar saque: {str(e)}", exc_info=True)
            messages.error(
                self.request, "Erro ao processar saque. Por favor, tente novamente."
            )
            return self.form_invalid(form)

        return super().form_valid(form)
