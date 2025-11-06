from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, FormView, DetailView
from django.shortcuts import get_object_or_404, redirect

from .pix_models import PIXKey, PIXTransaction, PIXQRCode
from .pix_forms import PIXKeyForm, PIXTransferForm, PIXQRCodeForm
from .pix_services import PIXService

User = get_user_model()


class PIXKeyListView(ListView):
    template_name = 'transactions/pix/key_list.html'
    model = PIXKey
    context_object_name = 'pix_keys'
    
    def get_queryset(self):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user:
            return PIXKey.objects.filter(user=demo_user, is_active=True)
        return PIXKey.objects.none()


class PIXKeyCreateView(CreateView):
    template_name = 'transactions/pix/key_create.html'
    form_class = PIXKeyForm
    success_url = reverse_lazy('transactions:pix_key_list')
    
    def form_valid(self, form):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user:
            messages.error(self.request, 'Usuário não encontrado')
            return self.form_invalid(form)
        
        try:
            pix_key = PIXService.register_pix_key(
                user=demo_user,
                key_type=form.cleaned_data['key_type'],
                key_value=form.cleaned_data['key_value']
            )
            
            from core.audit import AuditLogger
            AuditLogger.log_pix_key_registration(demo_user, pix_key)
            
            messages.success(self.request, 'Chave PIX registrada com sucesso!')
            return redirect(self.success_url)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class PIXKeyDeleteView(DeleteView):
    model = PIXKey
    success_url = reverse_lazy('transactions:pix_key_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, 'Chave PIX desativada com sucesso!')
        return redirect(self.success_url)


class PIXTransferView(FormView):
    template_name = 'transactions/pix/transfer.html'
    form_class = PIXTransferForm
    success_url = reverse_lazy('transactions:transaction_report')
    
    def form_valid(self, form):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user or not hasattr(demo_user, 'account'):
            messages.error(self.request, 'Conta não encontrada')
            return self.form_invalid(form)
        
        try:
            pix_transaction = PIXService.process_pix_transfer(
                from_account=demo_user.account,
                to_key_value=form.cleaned_data['to_key'],
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data.get('description', '')
            )
            
            from core.audit import AuditLogger
            AuditLogger.log_pix_transfer(demo_user, pix_transaction)
            
            messages.success(
                self.request,
                f'Transferência PIX realizada com sucesso! ID: {pix_transaction.end_to_end_id}'
            )
            return super().form_valid(form)
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class PIXQRCodeGenerateView(FormView):
    template_name = 'transactions/pix/qr_code_generate.html'
    form_class = PIXQRCodeForm
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user:
            form.fields['pix_key_id'].widget.choices = [
                (key.id, f"{key.get_key_type_display()}: {key.key_value}") 
                for key in PIXKey.objects.filter(user=demo_user, is_active=True)
            ]
        return form
    
    def form_valid(self, form):
        demo_user = User.objects.filter(email='demo@example.com').first()
        if not demo_user:
            messages.error(self.request, 'Usuário não encontrado')
            return self.form_invalid(form)
        
        pix_key = get_object_or_404(PIXKey, id=form.cleaned_data['pix_key_id'], user=demo_user)
        
        qr_code = PIXService.generate_qr_code(
            pix_key=pix_key,
            amount=form.cleaned_data.get('amount'),
            description=form.cleaned_data.get('description', '')
        )
        
        from core.audit import AuditLogger
        AuditLogger.log_action(
            user=demo_user,
            action='PIX_GENERATE_QR',
            resource_type='PIXQRCode',
            resource_id=qr_code.id,
            details={'pix_key': pix_key.key_value}
        )
        
        messages.success(self.request, 'QR Code gerado com sucesso!')
        return redirect('transactions:pix_qr_code_view', pk=qr_code.id)


class PIXQRCodeView(DetailView):
    template_name = 'transactions/pix/qr_code_view.html'
    model = PIXQRCode
    context_object_name = 'qr_code'
