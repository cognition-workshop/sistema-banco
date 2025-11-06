import qrcode
import json
import io
import base64
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from .models import PixKey, PixTransaction
from .forms import PixKeyForm, PixTransferForm


class PixKeyListView(ListView):
    model = PixKey
    template_name = 'pix/key_list.html'
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
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        return context


class PixKeyCreateView(CreateView):
    model = PixKey
    form_class = PixKeyForm
    template_name = 'pix/key_form.html'
    success_url = reverse_lazy('pix:key_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Chave PIX cadastrada com sucesso!'
        )
        return super().form_valid(form)


class PixTransferView(View):
    template_name = 'pix/transfer_form.html'
    
    def get(self, request):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(request, 'Conta não encontrada')
            return redirect('home')
        
        form = PixTransferForm(account=demo_user.account)
        return render(request, self.template_name, {
            'form': form,
            'account': demo_user.account
        })
    
    def post(self, request):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(request, 'Conta não encontrada')
            return redirect('home')
        
        form = PixTransferForm(request.POST, account=demo_user.account)
        
        if form.is_valid():
            receiver_key = form.receiver_pix_key
            amount = form.cleaned_data['amount']
            sender_account = demo_user.account
            receiver_account = receiver_key.account
            
            sender_key = PixKey.objects.filter(account=sender_account).first()
            
            try:
                with transaction.atomic():
                    sender_account.balance -= amount
                    receiver_account.balance += amount
                    
                    sender_account.save(update_fields=['balance'])
                    receiver_account.save(update_fields=['balance'])
                    
                    PixTransaction.objects.create(
                        sender_account=sender_account,
                        receiver_account=receiver_account,
                        sender_key=sender_key,
                        receiver_key=receiver_key,
                        amount=amount,
                        sender_balance_after=sender_account.balance,
                        receiver_balance_after=receiver_account.balance,
                    )
                    
                    messages.success(
                        request,
                        f'Transferência PIX de R$ {amount} realizada com sucesso!'
                    )
                    return redirect('pix:transaction_list')
            
            except Exception as e:
                messages.error(
                    request,
                    f'Erro ao processar transferência: {str(e)}'
                )
        
        return render(request, self.template_name, {
            'form': form,
            'account': demo_user.account
        })


class PixTransactionListView(ListView):
    model = PixTransaction
    template_name = 'pix/transaction_list.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            return PixTransaction.objects.none()
        
        account = demo_user.account
        return PixTransaction.objects.filter(
            sender_account=account
        ) | PixTransaction.objects.filter(
            receiver_account=account
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        return context


class PixQRCodeView(View):
    def get(self, request, key_id):
        try:
            pix_key = PixKey.objects.get(id=key_id)
            
            pix_data = {
                'key': pix_key.key_value,
                'key_type': pix_key.get_key_type_display(),
                'account_no': str(pix_key.account.account_no),
                'name': pix_key.account.user.get_full_name() or pix_key.account.user.email,
            }
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(json.dumps(pix_data))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return JsonResponse({
                'qr_code': f'data:image/png;base64,{img_str}',
                'pix_data': pix_data
            })
        
        except PixKey.DoesNotExist:
            return JsonResponse({'error': 'Chave PIX não encontrada'}, status=404)
