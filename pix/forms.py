from django import forms
from .models import PixKey
from .constants import CPF_KEY, EMAIL_KEY, PHONE_KEY
from accounts.models import validate_cpf


class PixKeyForm(forms.ModelForm):
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value']
    
    def __init__(self, *args, **kwargs):
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
        
        if key_type == CPF_KEY and key_value:
            validate_cpf(key_value)
        elif key_type == EMAIL_KEY and key_value:
            if '@' not in key_value:
                raise forms.ValidationError('E-mail inválido')
        elif key_type == PHONE_KEY and key_value:
            phone = ''.join(filter(str.isdigit, key_value))
            if len(phone) < 10 or len(phone) > 11:
                raise forms.ValidationError('Telefone inválido')
        
        return cleaned_data


class PixTransferForm(forms.Form):
    pix_key = forms.CharField(
        max_length=255,
        label='Chave PIX',
        help_text='CPF, e-mail, telefone ou chave aleatória'
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
        label='Descrição'
    )
    
    def __init__(self, *args, **kwargs):
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
