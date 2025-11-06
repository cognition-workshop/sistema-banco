from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid

from .pix_forms import PIXKeyRegistrationForm, PIXTransferForm
from .models import PIXKey, PIXTransaction, Transaction
from .constants import PIX_TRANSFER
from accounts.models import UserBankAccount


@login_required
def pix_key_list(request):
    pix_keys = PIXKey.objects.filter(user=request.user)
    return render(request, 'transactions/pix_key_list.html', {
        'pix_keys': pix_keys
    })


@login_required
def pix_key_register(request):
    if request.method == 'POST':
        form = PIXKeyRegistrationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Chave PIX cadastrada com sucesso!')
            return redirect('pix_key_list')
    else:
        form = PIXKeyRegistrationForm(user=request.user)
    
    return render(request, 'transactions/pix_key_register.html', {
        'form': form
    })


@login_required
def pix_key_deactivate(request, key_id):
    pix_key = get_object_or_404(PIXKey, id=key_id, user=request.user)
    pix_key.is_active = False
    pix_key.save()
    messages.success(request, 'Chave PIX desativada com sucesso!')
    return redirect('pix_key_list')


@login_required
@transaction.atomic
def pix_transfer(request):
    account = get_object_or_404(UserBankAccount, user=request.user)
    
    if request.method == 'POST':
        form = PIXTransferForm(request.POST, account=account)
        if form.is_valid():
            pix_key_value = form.cleaned_data['pix_key']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')
            
            receiver_pix_key = PIXKey.objects.get(key_value=pix_key_value, is_active=True)
            receiver_account = receiver_pix_key.user.account
            
            account.balance -= amount
            account.save()
            
            sender_transaction = Transaction.objects.create(
                account=account,
                amount=-amount,
                balance_after_transaction=account.balance,
                transaction_type=PIX_TRANSFER
            )
            
            receiver_account.balance += amount
            receiver_account.save()
            
            receiver_transaction = Transaction.objects.create(
                account=receiver_account,
                amount=amount,
                balance_after_transaction=receiver_account.balance,
                transaction_type=PIX_TRANSFER
            )
            
            e2e_id = f'E{timezone.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:10].upper()}'
            
            PIXTransaction.objects.create(
                transaction=sender_transaction,
                e2e_id=e2e_id,
                payer_info={
                    'cpf': account.user.cpf,
                    'name': f'{account.user.first_name} {account.user.last_name}',
                    'account': account.get_formatted_account()
                },
                payee_info={
                    'cpf': receiver_account.user.cpf,
                    'name': f'{receiver_account.user.first_name} {receiver_account.user.last_name}',
                    'account': receiver_account.get_formatted_account()
                },
                pix_key_used=pix_key_value
            )
            
            messages.success(request, f'Transferência PIX realizada com sucesso! E2E ID: {e2e_id}')
            return redirect('transaction_report')
    else:
        form = PIXTransferForm(account=account)
    
    return render(request, 'transactions/pix_transfer.html', {
        'form': form,
        'account': account
    })
