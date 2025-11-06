from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, FormView
from .models import PixKey, PixTransaction, PixQRCode
from .forms import PixKeyRegistrationForm, PixTransferForm
from transactions.models import Transaction
from transactions.constants import PIX_TRANSFER


class PixKeyListView(LoginRequiredMixin, ListView):
    model = PixKey
    template_name = 'pix/key_list.html'
    context_object_name = 'pix_keys'

    def get_queryset(self):
        return PixKey.objects.filter(account=self.request.user.account)


class PixKeyCreateView(LoginRequiredMixin, CreateView):
    model = PixKey
    form_class = PixKeyRegistrationForm
    template_name = 'pix/key_form.html'
    success_url = reverse_lazy('pix:key_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['account'] = self.request.user.account
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Chave PIX cadastrada com sucesso!')
        return super().form_valid(form)


class PixTransferView(LoginRequiredMixin, FormView):
    form_class = PixTransferForm
    template_name = 'pix/transfer_form.html'
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['account'] = self.request.user.account
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        pix_key = form.cleaned_data['pix_key']
        amount = form.cleaned_data['amount']
        description = form.cleaned_data.get('description', '')

        sender_account = self.request.user.account
        receiver_account = pix_key.account

        sender_account.balance -= amount
        sender_account.save(update_fields=['balance'])

        receiver_account.balance += amount
        receiver_account.save(update_fields=['balance'])

        sender_transaction = Transaction.objects.create(
            account=sender_account,
            amount=amount,
            balance_after_transaction=sender_account.balance,
            transaction_type=PIX_TRANSFER
        )

        receiver_transaction = Transaction.objects.create(
            account=receiver_account,
            amount=amount,
            balance_after_transaction=receiver_account.balance,
            transaction_type=PIX_TRANSFER
        )

        PixTransaction.objects.create(
            transaction=sender_transaction,
            pix_key_used=pix_key,
            sender_account=sender_account,
            receiver_account=receiver_account,
            description=description
        )

        messages.success(
            self.request,
            f'Transferência PIX de R$ {amount} realizada com sucesso!'
        )
        return super().form_valid(form)


class PixQRCodeCreateView(LoginRequiredMixin, CreateView):
    model = PixQRCode
    template_name = 'pix/qrcode_form.html'
    fields = ['pix_key', 'amount', 'description']
    success_url = reverse_lazy('pix:qrcode_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['pix_key'].queryset = PixKey.objects.filter(
            account=self.request.user.account,
            is_active=True
        )
        return form

    def form_valid(self, form):
        import qrcode
        from io import BytesIO
        from django.core.files import File

        qr_code = form.save(commit=False)
        qr_code.account = self.request.user.account

        payload = {
            'key': qr_code.pix_key.key_value,
            'amount': float(qr_code.amount) if qr_code.amount else None,
            'description': qr_code.description
        }
        import json
        qr_code.qr_code_payload = json.dumps(payload)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code.qr_code_payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'pix_qr_{qr_code.pix_key.id}.png'
        qr_code.qr_code_image.save(file_name, File(buffer), save=False)
        buffer.close()

        qr_code.save()
        messages.success(self.request, 'QR Code PIX gerado com sucesso!')
        return super().form_valid(form)


class PixQRCodeListView(LoginRequiredMixin, ListView):
    model = PixQRCode
    template_name = 'pix/qrcode_list.html'
    context_object_name = 'qr_codes'

    def get_queryset(self):
        return PixQRCode.objects.filter(account=self.request.user.account)
