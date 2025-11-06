import logging
from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import transaction, OperationalError, IntegrityError
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

logger = logging.getLogger('transactions')
audit_logger = logging.getLogger('audit')


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
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        
        if not account:
            logger.warning(
                'Deposit attempt failed - no account found',
                extra={
                    'transaction_type': 'DEPOSIT',
                    'amount': amount,
                }
            )
            logger.error('Demo user account not found for deposit operation')
            messages.error(
                self.request,
                'Account not found. Please contact support.'
            )
            return super().form_invalid(form)

        try:
            with transaction.atomic():
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
                    'Deposit completed successfully',
                    extra={
                        'user_email': demo_user.email,
                        'account_no': account.account_no,
                        'amount': amount,
                        'transaction_type': 'DEPOSIT',
                        'balance_after': account.balance,
                    }
                )

                audit_logger.info(
                    f'Deposit successful',
                    extra={
                        'user': str(demo_user),
                        'action': 'DEPOSIT',
                        'amount': str(amount),
                        'new_balance': str(account.balance),
                    }
                )

                messages.success(
                    self.request,
                    f'{amount}$ was deposited to your account successfully'
                )

                return super().form_valid(form)

        except (OperationalError, IntegrityError) as e:
            logger.error(f'Database error during deposit: {str(e)}', exc_info=True)
            audit_logger.warning(
                f'Deposit failed - Database error',
                extra={
                    'user': str(demo_user),
                    'action': 'DEPOSIT_FAILED',
                    'amount': str(amount),
                    'error': str(e),
                }
            )
            messages.error(
                self.request,
                'Transaction failed due to a system error. Please try again later.'
            )
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error during deposit: {str(e)}', exc_info=True)
            audit_logger.warning(
                f'Deposit failed - Unexpected error',
                extra={
                    'user': str(demo_user),
                    'action': 'DEPOSIT_FAILED',
                    'amount': str(amount),
                    'error': str(e),
                }
            )
            messages.error(
                self.request,
                'An unexpected error occurred. Please try again later.'
            )
            return super().form_invalid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            logger.warning(
                'Withdrawal attempt failed - no account found',
                extra={
                    'transaction_type': 'WITHDRAWAL',
                    'amount': amount,
                }
            )
            logger.error('Demo user account not found for withdrawal operation')
            messages.error(
                self.request,
                'Account not found. Please contact support.'
            )
            return super().form_invalid(form)
        
        try:
            with transaction.atomic():
                account = demo_user.account
                
                if account.balance < amount:
                    logger.warning(
                        f'Withdrawal attempt with insufficient balance: '
                        f'User={demo_user}, Amount={amount}, Balance={account.balance}'
                    )
                    audit_logger.warning(
                        f'Withdrawal blocked - Insufficient balance',
                        extra={
                            'user': str(demo_user),
                            'action': 'WITHDRAWAL_BLOCKED',
                            'amount': str(amount),
                            'balance': str(account.balance),
                        }
                    )
                    messages.error(
                        self.request,
                        f'Insufficient balance. Your current balance is {account.balance} $'
                    )
                    return super().form_invalid(form)
                
                account.balance -= amount
                account.save(update_fields=['balance'])

                logger.info(
                    'Withdrawal completed successfully',
                    extra={
                        'user_email': demo_user.email,
                        'account_no': demo_user.account.account_no,
                        'amount': amount,
                        'transaction_type': 'WITHDRAWAL',
                        'balance_after': demo_user.account.balance,
                    }
                )

                audit_logger.info(
                    f'Withdrawal successful',
                    extra={
                        'user': str(demo_user),
                        'action': 'WITHDRAWAL',
                        'amount': str(amount),
                        'new_balance': str(account.balance),
                    }
                )

                messages.success(
                    self.request,
                    f'Successfully withdrawn {amount}$ from your account'
                )

                return super().form_valid(form)

        except (OperationalError, IntegrityError) as e:
            logger.error(f'Database error during withdrawal: {str(e)}', exc_info=True)
            audit_logger.warning(
                f'Withdrawal failed - Database error',
                extra={
                    'user': str(demo_user),
                    'action': 'WITHDRAWAL_FAILED',
                    'amount': str(amount),
                    'error': str(e),
                }
            )
            messages.error(
                self.request,
                'Transaction failed due to a system error. Please try again later.'
            )
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error during withdrawal: {str(e)}', exc_info=True)
            audit_logger.warning(
                f'Withdrawal failed - Unexpected error',
                extra={
                    'user': str(demo_user),
                    'action': 'WITHDRAWAL_FAILED',
                    'amount': str(amount),
                    'error': str(e),
                }
            )
            messages.error(
                self.request,
                'An unexpected error occurred. Please try again later.'
            )
            return super().form_invalid(form)
