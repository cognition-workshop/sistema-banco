from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import PixKey, PixTransaction
from accounts.models import UserBankAccount


@login_required
def register_pix_key(request):
    if request.method == 'POST':
        key_type = request.POST.get('key_type')
        key_value = request.POST.get('key_value')
        
        try:
            account = UserBankAccount.objects.get(user=request.user)
            pix_key = PixKey.objects.create(
                account=account,
                key_type=key_type,
                key_value=key_value
            )
            messages.success(request, f'PIX key {pix_key.key_value} registered successfully!')
            return redirect('pix_keys')
        except Exception as e:
            messages.error(request, f'Error registering PIX key: {str(e)}')
    
    return render(request, 'pix/register_key.html')


@login_required
def list_pix_keys(request):
    account = UserBankAccount.objects.get(user=request.user)
    pix_keys = PixKey.objects.filter(account=account, is_active=True)
    return render(request, 'pix/list_keys.html', {'pix_keys': pix_keys})


@login_required
def delete_pix_key(request, key_id):
    pix_key = get_object_or_404(PixKey, id=key_id, account__user=request.user)
    pix_key.is_active = False
    pix_key.save()
    messages.success(request, 'PIX key deactivated successfully!')
    return redirect('pix_keys')


@login_required
def create_pix_transfer(request):
    if request.method == 'POST':
        receiver_key_value = request.POST.get('receiver_key')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        
        try:
            sender_account = UserBankAccount.objects.get(user=request.user)
            receiver_key = PixKey.objects.get(key_value=receiver_key_value, is_active=True)
            
            with transaction.atomic():
                pix_transaction = PixTransaction.objects.create(
                    sender_account=sender_account,
                    receiver_key=receiver_key,
                    amount=amount,
                    description=description,
                    ip_address=getattr(request, 'audit_ip', None),
                    geolocation=getattr(request, 'audit_geolocation', None),
                    channel=getattr(request, 'audit_channel', None),
                )
                
                if pix_transaction.process_transaction():
                    pix_transaction.generate_qr_code()
                    messages.success(request, f'PIX transfer of R${amount} completed successfully!')
                    return redirect('pix_transaction_detail', transaction_id=pix_transaction.transaction_id)
                else:
                    messages.error(request, f'PIX transfer failed: {pix_transaction.error_message}')
        
        except PixKey.DoesNotExist:
            messages.error(request, 'Invalid PIX key')
        except Exception as e:
            messages.error(request, f'Error processing PIX transfer: {str(e)}')
    
    return render(request, 'pix/create_transfer.html')


@login_required
def pix_transaction_detail(request, transaction_id):
    pix_transaction = get_object_or_404(PixTransaction, transaction_id=transaction_id)
    
    if pix_transaction.sender_account.user != request.user and pix_transaction.receiver_key.account.user != request.user:
        messages.error(request, 'You do not have permission to view this transaction')
        return redirect('home')
    
    return render(request, 'pix/transaction_detail.html', {'transaction': pix_transaction})


@login_required
def list_pix_transactions(request):
    account = UserBankAccount.objects.get(user=request.user)
    sent_transactions = PixTransaction.objects.filter(sender_account=account)
    received_transactions = PixTransaction.objects.filter(receiver_key__account=account)
    
    context = {
        'sent_transactions': sent_transactions,
        'received_transactions': received_transactions,
    }
    return render(request, 'pix/list_transactions.html', context)
