from django import forms
from django.conf import settings

from .models import PixKey, PixTransaction
from .constants import PIX_KEY_TYPE_CHOICES


class PixKeyForm(forms.ModelForm):
    
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
                account=self.account,
                key_type=key_type,
                key_value=key_value
            ).exists():
                raise forms.ValidationError(
                    'Esta chave PIX já está cadastrada para sua conta'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        self.instance.account = self.account
        return super().save(commit=commit)


class PixTransferForm(forms.Form):
    receiver_key = forms.CharField(
        max_length=255,
        label='Chave PIX do destinatário'
    )
    amount = forms.DecimalField(
        decimal_places=2,
        max_digits=12,
        label='Valor'
    )
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
    
    def clean_receiver_key(self):
        receiver_key = self.cleaned_data.get('receiver_key')
        
        try:
            self.receiver_pix_key = PixKey.objects.get(key_value=receiver_key)
        except PixKey.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada')
        
        if self.receiver_pix_key.account == self.account:
            raise forms.ValidationError(
                'Você não pode transferir para sua própria conta'
            )
        
        return receiver_key
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        balance = self.account.balance
        
        min_amount = getattr(settings, 'MINIMUM_PIX_AMOUNT', 0.01)
        
        if amount < min_amount:
            raise forms.ValidationError(
                f'Valor mínimo para transferência PIX: R$ {min_amount}'
            )
        
        if amount > balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Saldo disponível: R$ {balance}'
            )
        
        return amount
