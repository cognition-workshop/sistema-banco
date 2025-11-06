from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.http import HttpResponse

from .models import PixKey
from .forms import PixKeyRegistrationForm, PixTransferForm
from .utils import generate_pix_qr_code


class PixKeyCreateView(CreateView):
    model = PixKey
    form_class = PixKeyRegistrationForm
    template_name = 'pix/pix_key_form.html'
    success_url = reverse_lazy('pix:pix_key_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs.update({'account': demo_user.account})
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            'PIX key registered successfully'
        )
        return super().form_valid(form)


class PixKeyListView(ListView):
    model = PixKey
    template_name = 'pix/pix_key_list.html'
    context_object_name = 'pix_keys'

    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return PixKey.objects.filter(
                account=demo_user.account,
                is_active=True
            )
        return PixKey.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        context['account'] = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
        return context


class PixTransferView(CreateView):
    template_name = 'pix/pix_transfer_form.html'
    form_class = PixTransferForm
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            kwargs.update({'account': demo_user.account})
        return kwargs

    def form_valid(self, form):
        sender_transaction, receiver_transaction = form.execute_transfer()
        messages.success(
            self.request,
            f'Successfully transferred {form.cleaned_data["amount"]} $ via PIX'
        )
        return redirect(self.success_url)


class PixQRCodeView(CreateView):
    def get(self, request, *args, **kwargs):
        pix_key_id = kwargs.get('pk')
        try:
            pix_key = PixKey.objects.get(id=pix_key_id, is_active=True)
            qr_code_data = generate_pix_qr_code(pix_key.key_value)
            return HttpResponse(qr_code_data, content_type='image/png')
        except PixKey.DoesNotExist:
            return HttpResponse('PIX key not found', status=404)
