from django import forms
from .models import PixKey, PixTransaction
from .constants import PIX_KEY_TYPE_CHOICES
from accounts.models import UserBankAccount


class PixKeyRegistrationForm(forms.ModelForm):
    """Form to register a new PIX key"""
    
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value']
        
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        
    def clean_key_value(self):
        key_value = self.cleaned_data.get('key_value')
        key_type = self.cleaned_data.get('key_type')
        
        if key_type == 'CPF':
            from accounts.validators import validate_cpf_digits
            validate_cpf_digits(key_value)
        elif key_type == 'EMAIL':
            from django.core.validators import validate_email
            validate_email(key_value)
        elif key_type == 'PHONE':
            import re
            if not re.match(r'^\+?55\d{10,11}$', key_value):
                raise forms.ValidationError('Telefone deve estar no formato +5511999999999')
        
        return key_value
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.account = self.account
        if commit:
            instance.save()
        return instance


class PixTransferForm(forms.Form):
    """Form for PIX transfers"""
    pix_key = forms.CharField(
        max_length=255,
        label='Chave PIX do destinatário'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label='Valor'
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        label='Descrição (opcional)'
    )
    
    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
    
    def clean_pix_key(self):
        pix_key = self.cleaned_data.get('pix_key')
        try:
            self.receiver_key = PixKey.objects.get(
                key_value=pix_key,
                is_active=True
            )
        except PixKey.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada')
        
        if self.receiver_key.account == self.sender_account:
            raise forms.ValidationError('Não é possível transferir para a própria conta')
        
        return pix_key
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount > self.sender_account.balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Saldo disponível: R$ {self.sender_account.balance}'
            )
        
        return amount
