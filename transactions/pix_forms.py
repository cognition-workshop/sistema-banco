from django import forms
from django.conf import settings
from .models import PIXKey, Transaction
from .constants import PIX_KEY_TYPES, PIX_TRANSFER
from accounts.models import UserBankAccount
import uuid


class PIXKeyRegistrationForm(forms.ModelForm):
    class Meta:
        model = PIXKey
        fields = ['key_type', 'key_value']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })
    
    def clean_key_value(self):
        key_value = self.cleaned_data.get('key_value')
        key_type = self.cleaned_data.get('key_type')
        
        if PIXKey.objects.filter(key_value=key_value).exists():
            raise forms.ValidationError('Esta chave PIX já está cadastrada')
        
        return key_value
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class PIXTransferForm(forms.Form):
    pix_key = forms.CharField(
        max_length=255,
        label='Chave PIX',
        help_text='CPF, Email, Telefone ou Chave Aleatória'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label='Valor (R$)'
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        label='Descrição'
    )
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })
    
    def clean_pix_key(self):
        pix_key = self.cleaned_data.get('pix_key')
        
        try:
            pix_key_obj = PIXKey.objects.get(key_value=pix_key, is_active=True)
        except PIXKey.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada ou inativa')
        
        if pix_key_obj.user == self.account.user:
            raise forms.ValidationError('Você não pode transferir para sua própria chave PIX')
        
        return pix_key
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise forms.ValidationError('O valor deve ser maior que zero')
        
        if self.account and amount > self.account.balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Saldo disponível: R$ {self.account.balance}'
            )
        
        return amount
