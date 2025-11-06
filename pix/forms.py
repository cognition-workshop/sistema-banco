from django import forms
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import PixKey, PixKeyType
from transactions.models import Transaction
from transactions.constants import PIX_TRANSFER


class PixKeyRegistrationForm(forms.ModelForm):
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        key_type = cleaned_data.get('key_type')
        key_value = cleaned_data.get('key_value')

        if key_type and key_value:
            if PixKey.objects.filter(
                key_type=key_type,
                key_value=key_value,
                is_active=True
            ).exists():
                raise forms.ValidationError(
                    'This PIX key is already registered'
                )

        return cleaned_data

    def save(self, commit=True):
        self.instance.account = self.account
        return super().save(commit)


class PixTransferForm(forms.Form):
    pix_key = forms.CharField(max_length=255, label='PIX Key')
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label='Amount'
    )

    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        balance = self.sender_account.balance

        min_transfer_amount = getattr(settings, 'MINIMUM_PIX_TRANSFER_AMOUNT', 0.01)

        if amount < min_transfer_amount:
            raise forms.ValidationError(
                f'Minimum transfer amount is {min_transfer_amount} $'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {balance} $'
            )

        return amount

    def clean_pix_key(self):
        pix_key_value = self.cleaned_data.get('pix_key')

        try:
            pix_key = PixKey.objects.select_related('account').get(
                key_value=pix_key_value,
                is_active=True
            )
        except PixKey.DoesNotExist:
            raise forms.ValidationError('PIX key not found')

        if pix_key.account == self.sender_account:
            raise forms.ValidationError('Cannot transfer to your own account')

        self.cleaned_data['pix_key_obj'] = pix_key
        return pix_key_value

    def execute_transfer(self):
        amount = self.cleaned_data['amount']
        pix_key = self.cleaned_data['pix_key_obj']
        receiver_account = pix_key.account

        with transaction.atomic():
            self.sender_account.balance -= amount
            self.sender_account.save(update_fields=['balance'])

            receiver_account.balance += amount
            receiver_account.save(update_fields=['balance'])

            sender_transaction = Transaction.objects.create(
                account=self.sender_account,
                amount=-amount,
                balance_after_transaction=self.sender_account.balance,
                transaction_type=PIX_TRANSFER
            )

            receiver_transaction = Transaction.objects.create(
                account=receiver_account,
                amount=amount,
                balance_after_transaction=receiver_account.balance,
                transaction_type=PIX_TRANSFER
            )

        return sender_transaction, receiver_transaction
