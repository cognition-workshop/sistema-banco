from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ChavePix, TransacaoPix
from .forms import CadastroChavePixForm, TransferenciaPixForm
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL

User = get_user_model()


class CadastrarChavePixView(CreateView):
    model = ChavePix
    form_class = CadastroChavePixForm
    template_name = 'pix/cadastrar_chave.html'
    success_url = reverse_lazy('pix:minhas_chaves')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Chave PIX cadastrada com sucesso!')
        return response


class MinhasChavesPixView(ListView):
    model = ChavePix
    template_name = 'pix/minhas_chaves.html'
    context_object_name = 'chaves'
    
    def get_queryset(self):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return ChavePix.objects.filter(account=demo_user.account)
        return ChavePix.objects.none()


class DeletarChavePixView(DeleteView):
    model = ChavePix
    success_url = reverse_lazy('pix:minhas_chaves')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Chave PIX removida com sucesso!')
        return super().delete(request, *args, **kwargs)


class TransferirPixView(CreateView):
    model = TransacaoPix
    form_class = TransferenciaPixForm
    template_name = 'pix/transferir.html'
    success_url = reverse_lazy('pix:historico')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs['account'] = demo_user.account
        return kwargs
    
    @db_transaction.atomic
    def form_valid(self, form):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(self.request, 'Conta não encontrada.')
            return redirect('pix:transferir')
        
        conta_origem = demo_user.account
        chave_destino = form.cleaned_data['chave_destino']
        valor = form.cleaned_data['valor']
        
        try:
            chave_pix = ChavePix.objects.get(chave=chave_destino, ativa=True)
            conta_destino = chave_pix.account
            
            transacao_pix = form.save(commit=False)
            transacao_pix.conta_origem = conta_origem
            transacao_pix.conta_destino = conta_destino
            transacao_pix.status = 'CONCLUIDA'
            transacao_pix.save()
            
            conta_origem.balance -= valor
            conta_origem.save(update_fields=['balance'])
            
            conta_destino.balance += valor
            conta_destino.save(update_fields=['balance'])
            
            Transaction.objects.create(
                account=conta_origem,
                amount=valor,
                balance_after_transaction=conta_origem.balance,
                transaction_type=WITHDRAWAL
            )
            
            Transaction.objects.create(
                account=conta_destino,
                amount=valor,
                balance_after_transaction=conta_destino.balance,
                transaction_type=DEPOSIT
            )
            
            messages.success(
                self.request,
                f'PIX de R$ {valor} realizado com sucesso!'
            )
            return redirect(self.success_url)
            
        except ChavePix.DoesNotExist:
            messages.error(self.request, 'Chave PIX não encontrada.')
            return self.form_invalid(form)
        except Exception as e:
            transacao_pix = form.save(commit=False)
            transacao_pix.conta_origem = conta_origem
            transacao_pix.status = 'ERRO'
            transacao_pix.erro_mensagem = str(e)
            transacao_pix.save()
            
            messages.error(self.request, f'Erro ao processar PIX: {str(e)}')
            return self.form_invalid(form)


class HistoricoPixView(ListView):
    model = TransacaoPix
    template_name = 'pix/historico.html'
    context_object_name = 'transacoes'
    
    def get_queryset(self):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return TransacaoPix.objects.filter(
                conta_origem=demo_user.account
            ) | TransacaoPix.objects.filter(
                conta_destino=demo_user.account
            )
        return TransacaoPix.objects.none()
