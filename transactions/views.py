from dateutil.relativedelta import relativedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import models, transaction as db_transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView
import qrcode

from transactions.constants import DEPOSIT, WITHDRAWAL, PIX
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
    PixKeyForm,
    PixTransferForm,
    PixQRCodeForm,
    PixQRCodePaymentForm,
)
from transactions.models import Transaction, PixKey, PixTransaction, PixQRCode


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


class PixKeyManagementView(ListView):
    template_name = 'transactions/pix_keys.html'
    model = PixKey
    context_object_name = 'pix_keys'

    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return PixKey.objects.none()
        return PixKey.objects.filter(account=demo_user.account)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            context['form'] = PixKeyForm(account=demo_user.account)
            context['account'] = demo_user.account
        
        return context

    def post(self, request, *args, **kwargs):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(request, 'Conta não encontrada')
            return redirect('transactions:pix_keys')
        
        form = PixKeyForm(request.POST, account=demo_user.account)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Chave PIX cadastrada com sucesso!')
            return redirect('transactions:pix_keys')
        
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class PixTransferView(CreateView):
    template_name = 'transactions/pix_transfer.html'
    form_class = PixTransferForm
    success_url = reverse_lazy('transactions:pix_history')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        context['title'] = 'Transferência PIX'
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(self.request, 'Conta não encontrada')
            return redirect('transactions:pix_transfer')
        
        sender_account = demo_user.account
        receiver_pix_key = form.receiver_pix_key
        receiver_account = receiver_pix_key.account
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', '')

        sender_account.balance -= amount
        sender_account.save(update_fields=['balance'])

        receiver_account.balance += amount
        receiver_account.save(update_fields=['balance'])

        pix_transaction = PixTransaction.objects.create(
            sender_account=sender_account,
            receiver_account=receiver_account,
            pix_key_used=receiver_pix_key,
            amount=amount,
            description=description,
            status='COMPLETED'
        )

        Transaction.objects.create(
            account=sender_account,
            amount=amount,
            balance_after_transaction=sender_account.balance,
            transaction_type=PIX
        )

        Transaction.objects.create(
            account=receiver_account,
            amount=amount,
            balance_after_transaction=receiver_account.balance,
            transaction_type=PIX
        )

        messages.success(
            self.request,
            f'Transferência PIX de ${amount} realizada com sucesso para {receiver_pix_key.key_value}'
        )

        return super().form_valid(form)


class PixQRCodeGenerateView(CreateView):
    template_name = 'transactions/pix_qrcode.html'
    form_class = PixQRCodeForm
    success_url = reverse_lazy('transactions:pix_qrcode_generate')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user and hasattr(demo_user, 'account'):
            context['account'] = demo_user.account
            context['qr_codes'] = PixQRCode.objects.filter(
                account=demo_user.account,
                is_active=True
            ).order_by('-created_at')
        
        context['title'] = 'Gerar QR Code PIX'
        return context

    def form_valid(self, form):
        qr_code = form.save()
        
        qr_data = f"PIX:{qr_code.qr_code_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        messages.success(
            self.request,
            f'QR Code gerado com sucesso! ID: {qr_code.qr_code_id}'
        )
        
        return super().form_valid(form)


class PixQRCodePayView(CreateView):
    template_name = 'transactions/pix_qrcode_pay.html'
    form_class = PixQRCodePaymentForm
    success_url = reverse_lazy('transactions:pix_history')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        context['title'] = 'Pagar com QR Code PIX'
        return context

    @db_transaction.atomic
    def form_valid(self, form):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(self.request, 'Conta não encontrada')
            return redirect('transactions:pix_qrcode_pay')
        
        payer_account = demo_user.account
        qr_code = form.qr_code
        receiver_account = qr_code.account
        amount = form.cleaned_data['amount']

        payer_account.balance -= amount
        payer_account.save(update_fields=['balance'])

        receiver_account.balance += amount
        receiver_account.save(update_fields=['balance'])

        PixTransaction.objects.create(
            sender_account=payer_account,
            receiver_account=receiver_account,
            amount=amount,
            description=qr_code.description,
            status='COMPLETED'
        )

        Transaction.objects.create(
            account=payer_account,
            amount=amount,
            balance_after_transaction=payer_account.balance,
            transaction_type=PIX
        )

        Transaction.objects.create(
            account=receiver_account,
            amount=amount,
            balance_after_transaction=receiver_account.balance,
            transaction_type=PIX
        )

        if qr_code.amount:
            qr_code.is_active = False
            qr_code.save(update_fields=['is_active'])

        messages.success(
            self.request,
            f'Pagamento PIX de ${amount} realizado com sucesso!'
        )

        return super().form_valid(form)


class PixTransactionHistoryView(ListView):
    template_name = 'transactions/pix_history.html'
    model = PixTransaction
    context_object_name = 'pix_transactions'

    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return PixTransaction.objects.none()
        
        return PixTransaction.objects.filter(
            models.Q(sender_account=demo_user.account) | 
            models.Q(receiver_account=demo_user.account)
        ).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        return context
