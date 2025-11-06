from django import forms
from .models import PixKey, PixKeyType
from accounts.models import UserBankAccount


class PixKeyRegistrationForm(forms.ModelForm):
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value']

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

    def clean(self):
        cleaned_data = super().clean()
        key_type = cleaned_data.get('key_type')
        key_value = cleaned_data.get('key_value')

        if key_type == PixKeyType.CPF:
            from accounts.validators import validate_cpf
            validate_cpf(key_value)
        elif key_type == PixKeyType.EMAIL:
            from django.core.validators import validate_email
            validate_email(key_value)
        elif key_type == PixKeyType.PHONE:
            import re
            if not re.match(r'^\+?55\d{10,11}$', key_value):
                raise forms.ValidationError('Telefone inválido. Use formato: +5511999999999')
        elif key_type == PixKeyType.RANDOM:
            if not key_value:
                cleaned_data['key_value'] = PixKey.generate_random_key()

        return cleaned_data

    def save(self, commit=True):
        pix_key = super().save(commit=False)
        pix_key.account = self.account
        if commit:
            pix_key.save()
        return pix_key


class PixTransferForm(forms.Form):
    pix_key = forms.CharField(max_length=255, label='Chave PIX do Destinatário')
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        label='Valor'
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
        pix_key_value = self.cleaned_data.get('pix_key')
        try:
            pix_key = PixKey.objects.get(key_value=pix_key_value, is_active=True)
        except PixKey.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada.')
        
        if pix_key.account == self.account:
            raise forms.ValidationError('Não é possível transferir para sua própria conta.')
        
        return pix_key

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.account and amount > self.account.balance:
            raise forms.ValidationError('Saldo insuficiente.')
        return amount
