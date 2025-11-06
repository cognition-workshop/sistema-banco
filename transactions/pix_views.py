from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.utils import timezone

from .models import Transaction, PixKey, PixTransaction
from .pix_forms import PixKeyRegistrationForm, PixTransferForm
from .constants import PIX_SENT, PIX_RECEIVED


class PixKeyListView(ListView):
    """List all PIX keys for the user's account"""
    model = PixKey
    template_name = 'transactions/pix_keys.html'
    context_object_name = 'pix_keys'
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return PixKey.objects.none()
        return PixKey.objects.filter(account=demo_user.account)


class PixKeyRegisterView(CreateView):
    """Register a new PIX key"""
    model = PixKey
    form_class = PixKeyRegistrationForm
    template_name = 'transactions/pix_key_form.html'
    success_url = reverse_lazy('transactions:pix_keys')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Chave PIX registrada com sucesso!')
        return super().form_valid(form)


class PixTransferView(CreateView):
    """Process a PIX transfer"""
    template_name = 'transactions/pix_transfer_form.html'
    form_class = PixTransferForm
    success_url = reverse_lazy('transactions:transaction_report')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs
    
    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', '')
        receiver_key = form.receiver_key
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        sender_account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        
        if not sender_account:
            messages.error(self.request, 'Conta não encontrada')
            return redirect('transactions:transaction_report')
        
        receiver_account = receiver_key.account
        
        with db_transaction.atomic():
            sender_account.balance -= amount
            sender_account.save(update_fields=['balance'])
            
            sender_transaction = Transaction.objects.create(
                account=sender_account,
                amount=amount,
                balance_after_transaction=sender_account.balance,
                transaction_type=PIX_SENT
            )
            
            receiver_account.balance += amount
            receiver_account.save(update_fields=['balance'])
            
            receiver_transaction = Transaction.objects.create(
                account=receiver_account,
                amount=amount,
                balance_after_transaction=receiver_account.balance,
                transaction_type=PIX_RECEIVED
            )
            
            PixTransaction.objects.create(
                transaction=sender_transaction,
                sender_account=sender_account,
                receiver_account=receiver_account,
                pix_key_used=receiver_key,
                description=description
            )
            
            PixTransaction.objects.create(
                transaction=receiver_transaction,
                sender_account=sender_account,
                receiver_account=receiver_account,
                pix_key_used=receiver_key,
                description=description
            )
        
        messages.success(
            self.request,
            f'PIX de R$ {amount} enviado com sucesso para {receiver_key.key_value}!'
        )
        return super().form_valid(form)
