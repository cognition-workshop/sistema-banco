from django import forms
from django.core.exceptions import ValidationError
from .models import PixKey, PixTransaction
from accounts.models import UserBankAccount
from accounts.validators import validate_cpf, clean_cpf


class PixKeyRegistrationForm(forms.ModelForm):
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value']
    
    def clean(self):
        cleaned_data = super().clean()
        key_type = cleaned_data.get('key_type')
        key_value = cleaned_data.get('key_value')
        
        if key_type == 'CPF':
            try:
                validate_cpf(key_value)
            except ValidationError as e:
                raise ValidationError({'key_value': e})
        
        elif key_type == 'EMAIL':
            from django.core.validators import EmailValidator
            validator = EmailValidator()
            try:
                validator(key_value)
            except ValidationError:
                raise ValidationError({'key_value': 'Email inválido.'})
        
        elif key_type == 'PHONE':
            import re
            phone = re.sub(r'[^0-9]', '', key_value)
            if len(phone) < 10 or len(phone) > 11:
                raise ValidationError({'key_value': 'Telefone inválido.'})
        
        return cleaned_data


class PixTransferForm(forms.Form):
    pix_key = forms.CharField(max_length=255, label='Chave PIX')
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01, label='Valor')
    description = forms.CharField(max_length=255, required=False, label='Descrição')
    
    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('sender_account')
        super().__init__(*args, **kwargs)
    
    def clean_pix_key(self):
        pix_key_value = self.cleaned_data.get('pix_key')
        
        try:
            pix_key = PixKey.objects.get(key_value=pix_key_value, is_active=True)
        except PixKey.DoesNotExist:
            raise ValidationError('Chave PIX não encontrada.')
        
        if pix_key.account == self.sender_account:
            raise ValidationError('Não é possível transferir para sua própria conta.')
        
        return pix_key
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount > self.sender_account.balance:
            raise ValidationError('Saldo insuficiente.')
        
        return amount


class PixQRCodeForm(forms.Form):
    pix_key = forms.ModelChoiceField(queryset=None, label='Chave PIX')
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label='Valor (deixe em branco para valor dinâmico)'
    )
    description = forms.CharField(max_length=255, required=False, label='Descrição')
    
    def __init__(self, *args, **kwargs):
        account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['pix_key'].queryset = PixKey.objects.filter(account=account, is_active=True)
