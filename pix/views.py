from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.db import transaction as db_transaction
from django.http import HttpResponse
import qrcode
from io import BytesIO

from .models import PixKey, PixTransaction
from .forms import PixKeyForm, PixTransferForm
from transactions.models import Transaction
from transactions.constants import WITHDRAWAL, DEPOSIT


class PixKeyCreateView(LoginRequiredMixin, CreateView):
    model = PixKey
    form_class = PixKeyForm
    template_name = 'pix/register_key.html'
    success_url = reverse_lazy('pix:list_keys')
    
    def form_valid(self, form):
        form.instance.account = self.request.user.account
        messages.success(self.request, 'Chave PIX cadastrada com sucesso!')
        return super().form_valid(form)


class PixKeyListView(LoginRequiredMixin, ListView):
    model = PixKey
    template_name = 'pix/list_keys.html'
    context_object_name = 'pix_keys'
    
    def get_queryset(self):
        return PixKey.objects.filter(account=self.request.user.account, is_active=True)


class PixTransferView(LoginRequiredMixin, CreateView):
    template_name = 'pix/transfer.html'
    form_class = PixTransferForm
    success_url = reverse_lazy('transactions:transaction_report')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.request.user.account
        return context
    
    def form_valid(self, form):
        pix_key_value = form.cleaned_data['pix_key']
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', '')
        
        try:
            pix_key = PixKey.objects.get(key_value=pix_key_value, is_active=True)
        except PixKey.DoesNotExist:
            messages.error(self.request, 'Chave PIX não encontrada')
            return self.form_invalid(form)
        
        if pix_key.account == self.request.user.account:
            messages.error(self.request, 'Não é possível transferir para sua própria conta')
            return self.form_invalid(form)
        
        if self.request.user.account.balance < amount:
            messages.error(self.request, 'Saldo insuficiente')
            return self.form_invalid(form)
        
        with db_transaction.atomic():
            sender_account = self.request.user.account
            sender_account.balance -= amount
            sender_account.save(update_fields=['balance'])
            
            withdrawal_txn = Transaction.objects.create(
                account=sender_account,
                amount=amount,
                balance_after_transaction=sender_account.balance,
                transaction_type=WITHDRAWAL
            )
            
            receiver_account = pix_key.account
            receiver_account.balance += amount
            receiver_account.save(update_fields=['balance'])
            
            Transaction.objects.create(
                account=receiver_account,
                amount=amount,
                balance_after_transaction=receiver_account.balance,
                transaction_type=DEPOSIT
            )
            
            PixTransaction.objects.create(
                from_account=sender_account,
                to_key=pix_key,
                amount=amount,
                description=description,
                transaction=withdrawal_txn
            )
        
        messages.success(
            self.request,
            f'Transferência PIX de R$ {amount} realizada com sucesso!'
        )
        return super().form_valid(form)


def generate_pix_qr_code(request, key_id):
    """Generate QR code for a PIX key"""
    try:
        pix_key = PixKey.objects.get(id=key_id, account=request.user.account)
    except PixKey.DoesNotExist:
        return HttpResponse('Chave PIX não encontrada', status=404)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(pix_key.key_value)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type='image/png')
