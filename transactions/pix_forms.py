from django import forms
from .pix_models import PIXKey, PIXKeyType


class PIXKeyForm(forms.Form):
    key_type = forms.ChoiceField(choices=PIXKeyType.choices, label='Tipo de Chave')
    key_value = forms.CharField(max_length=255, label='Valor da Chave')
    
    def clean_key_value(self):
        from accounts.validators import validate_cpf
        key_type = self.cleaned_data.get('key_type')
        key_value = self.cleaned_data.get('key_value')
        
        if key_type == 'CPF':
            try:
                validate_cpf(key_value)
            except Exception as e:
                raise forms.ValidationError(str(e))
        
        return key_value


class PIXTransferForm(forms.Form):
    to_key = forms.CharField(max_length=255, label='Chave PIX Destino')
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01, label='Valor')
    description = forms.CharField(max_length=500, required=False, widget=forms.Textarea, label='Descrição')


class PIXQRCodeForm(forms.Form):
    pix_key_id = forms.IntegerField(widget=forms.Select, label='Chave PIX')
    amount = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label='Valor (opcional)')
    description = forms.CharField(max_length=500, required=False, widget=forms.Textarea, label='Descrição')
