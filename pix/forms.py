from django import forms
from .models import ChavePix, TransacaoPix
from localflavor.br.forms import BRCPFField
from django.core.validators import EmailValidator

class CadastroChavePixForm(forms.ModelForm):
    class Meta:
        model = ChavePix
        fields = ['tipo', 'chave']
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
    
    def clean_chave(self):
        tipo = self.cleaned_data.get('tipo')
        chave = self.cleaned_data.get('chave')
        
        if tipo == 'CPF':
            cpf_field = BRCPFField()
            chave = cpf_field.clean(chave)
        elif tipo == 'EMAIL':
            validator = EmailValidator()
            validator(chave)
        elif tipo == 'TELEFONE':
            import re
            if not re.match(r'^\+?55?\d{10,11}$', chave.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')):
                raise forms.ValidationError('Formato de telefone inválido. Use formato: +5511999999999')
        elif tipo == 'ALEATORIA':
            chave = ChavePix.gerar_chave_aleatoria()
        
        if ChavePix.objects.filter(chave=chave).exists():
            raise forms.ValidationError('Esta chave PIX já está cadastrada.')
        
        return chave
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.account = self.account
        if commit:
            instance.save()
        return instance


class TransferenciaPixForm(forms.ModelForm):
    class Meta:
        model = TransacaoPix
        fields = ['chave_destino', 'valor', 'descricao']
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
    
    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        
        limite_pix_noturno = 1000
        limite_pix_diurno = 5000
        
        from django.utils import timezone
        hora_atual = timezone.now().hour
        
        if 20 <= hora_atual or hora_atual < 6:
            if valor > limite_pix_noturno:
                raise forms.ValidationError(
                    f'Limite PIX noturno (20h-6h) é R$ {limite_pix_noturno}.'
                )
        else:
            if valor > limite_pix_diurno:
                raise forms.ValidationError(
                    f'Limite PIX diurno é R$ {limite_pix_diurno}.'
                )
        
        if self.account and valor > self.account.balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Seu saldo atual é R$ {self.account.balance}'
            )
        
        return valor
    
    def clean_chave_destino(self):
        chave = self.cleaned_data.get('chave_destino')
        
        try:
            chave_pix = ChavePix.objects.get(chave=chave, ativa=True)
        except ChavePix.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada ou inativa.')
        
        if self.account and chave_pix.account == self.account:
            raise forms.ValidationError('Não é possível transferir para a própria conta.')
        
        return chave
