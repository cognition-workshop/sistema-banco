from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy

from .models import PixKey, PixTransaction, PixQRCode
from .forms import PixKeyRegistrationForm, PixTransferForm, PixQRCodeForm
from transactions.models import Transaction
from transactions.constants import PIX_TRANSFER
from transactions.views import get_client_ip


class PixKeyRegistrationView(CreateView):
    model = PixKey
    form_class = PixKeyRegistrationForm
    template_name = 'pix/register_key.html'
    success_url = reverse_lazy('pix:list_keys')
    
    def form_valid(self, form):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            form.instance.account = demo_user.account
        
        messages.success(self.request, 'Chave PIX registrada com sucesso!')
        return super().form_valid(form)


class PixKeyListView(ListView):
    model = PixKey
    template_name = 'pix/list_keys.html'
    context_object_name = 'pix_keys'
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return PixKey.objects.filter(account=demo_user.account)
        return PixKey.objects.none()


def pix_transfer_view(request):
    """Handle PIX transfer."""
    User = get_user_model()
    demo_user = User.objects.filter(email='demo@example.com').first()
    sender_account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
    
    if not sender_account:
        messages.error(request, 'Conta não encontrada.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PixTransferForm(request.POST, sender_account=sender_account)
        
        if form.is_valid():
            pix_key = form.cleaned_data['pix_key']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            recipient_account = pix_key.account
            
            with transaction.atomic():
                sender_account.balance -= amount
                sender_account.save()
                
                sender_transaction = Transaction.objects.create(
                    account=sender_account,
                    amount=-amount,
                    balance_after_transaction=sender_account.balance,
                    transaction_type=PIX_TRANSFER,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                recipient_account.balance += amount
                recipient_account.save()
                
                recipient_transaction = Transaction.objects.create(
                    account=recipient_account,
                    amount=amount,
                    balance_after_transaction=recipient_account.balance,
                    transaction_type=PIX_TRANSFER,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                PixTransaction.objects.create(
                    transaction=sender_transaction,
                    pix_key_used=pix_key,
                    recipient_account=recipient_account,
                    sender_account=sender_account,
                    description=description
                )
            
            messages.success(request, f'Transferência PIX de R$ {amount} realizada com sucesso!')
            return redirect('transactions:transaction_report')
    else:
        form = PixTransferForm(sender_account=sender_account)
    
    return render(request, 'pix/transfer.html', {'form': form})


def generate_qr_code_view(request):
    """Generate PIX QR code."""
    User = get_user_model()
    demo_user = User.objects.filter(email='demo@example.com').first()
    account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
    
    if not account:
        messages.error(request, 'Conta não encontrada.')
        return redirect('home')
    
    if request.method == 'POST':
        form = PixQRCodeForm(request.POST, account=account)
        
        if form.is_valid():
            qr_code = PixQRCode.objects.create(
                account=account,
                pix_key=form.cleaned_data['pix_key'],
                amount=form.cleaned_data.get('amount'),
                description=form.cleaned_data.get('description', '')
            )
            qr_code.generate_qr_code()
            qr_code.save()
            
            messages.success(request, 'QR Code PIX gerado com sucesso!')
            return redirect('pix:list_keys')
    else:
        form = PixQRCodeForm(account=account)
    
    return render(request, 'pix/generate_qrcode.html', {'form': form})
