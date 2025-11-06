import datetime
import re
import uuid

from django import forms
from django.conf import settings
from django.core.validators import EmailValidator
from validate_docbr import CPF

from .models import Transaction, PixKey, PixQRCode, PixTransaction


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):

    def clean_amount(self):
        min_deposit_amount = settings.MINIMUM_DEPOSIT_AMOUNT
        amount = self.cleaned_data.get('amount')

        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        max_withdraw_amount = (
            account.account_type.maximum_withdrawal_amount
        )
        balance = account.balance

        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        # TODO: Add validation to prevent negative balances
        # Bug: Users can currently withdraw more than their balance

        return amount


class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")
        print(daterange)

        try:
            daterange = daterange.split(' - ')
            print(daterange)
            if len(daterange) == 2:
                for date in daterange:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                return daterange
            else:
                raise forms.ValidationError("Please select a date range.")
        except (ValueError, AttributeError):
            raise forms.ValidationError("Invalid date range")


class PixKeyForm(forms.ModelForm):
    class Meta:
        model = PixKey
        fields = ['key_type', 'key_value', 'is_primary']
        
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        
        self.fields['key_value'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Digite sua chave PIX'
        })
        self.fields['key_type'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline'
        })

    def clean_key_value(self):
        key_type = self.cleaned_data.get('key_type')
        key_value = self.cleaned_data.get('key_value')
        
        if not key_value:
            raise forms.ValidationError('Chave PIX é obrigatória')
        
        if key_type == 'CPF':
            cpf_validator = CPF()
            clean_cpf = re.sub(r'[^\d]', '', key_value)
            if not cpf_validator.validate(clean_cpf):
                raise forms.ValidationError('CPF inválido')
            key_value = clean_cpf
            
        elif key_type == 'EMAIL':
            validator = EmailValidator()
            try:
                validator(key_value)
            except forms.ValidationError:
                raise forms.ValidationError('Email inválido')
                
        elif key_type == 'PHONE':
            clean_phone = re.sub(r'[^\d]', '', key_value)
            if clean_phone.startswith('55'):
                clean_phone = clean_phone[2:]
            if not re.match(r'^\d{10,11}$', clean_phone):
                raise forms.ValidationError('Telefone inválido. Use formato: (XX) XXXXX-XXXX')
            key_value = clean_phone
            
        elif key_type == 'RANDOM':
            if len(key_value) != 36:
                raise forms.ValidationError('Chave aleatória inválida')
        
        if PixKey.objects.filter(key_value=key_value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('Esta chave PIX já está cadastrada')
        
        return key_value
    
    def save(self, commit=True):
        self.instance.account = self.account
        return super().save(commit)


class PixTransferForm(forms.Form):
    pix_key = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Digite a chave PIX do destinatário'
        })
    )
    amount = forms.DecimalField(
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Valor da transferência',
            'step': '0.01'
        })
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Descrição (opcional)'
        })
    )

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def clean_pix_key(self):
        pix_key = self.cleaned_data.get('pix_key')
        try:
            self.receiver_pix_key = PixKey.objects.get(key_value=pix_key)
        except PixKey.DoesNotExist:
            raise forms.ValidationError('Chave PIX não encontrada')
        
        if self.receiver_pix_key.account == self.account:
            raise forms.ValidationError('Não é possível transferir para sua própria conta')
        
        return pix_key

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise forms.ValidationError('O valor deve ser maior que zero')
        
        if self.account.balance < amount:
            raise forms.ValidationError(
                f'Saldo insuficiente. Saldo disponível: ${self.account.balance}'
            )
        
        return amount


class PixQRCodeForm(forms.ModelForm):
    class Meta:
        model = PixQRCode
        fields = ['amount', 'description']
        
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        
        self.fields['amount'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Valor (deixe vazio para valor variável)',
            'step': '0.01'
        })
        self.fields['amount'].required = False
        self.fields['description'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Descrição do pagamento'
        })

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('O valor deve ser maior que zero')
        return amount
    
    def save(self, commit=True):
        self.instance.account = self.account
        return super().save(commit)


class PixQRCodePaymentForm(forms.Form):
    qr_code_id = forms.UUIDField(
        widget=forms.TextInput(attrs={
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'ID do QR Code'
        })
    )
    amount = forms.DecimalField(
        decimal_places=2,
        max_digits=12,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
            'placeholder': 'Valor (apenas para QR Code com valor variável)',
            'step': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

    def clean_qr_code_id(self):
        qr_code_id = self.cleaned_data.get('qr_code_id')
        try:
            self.qr_code = PixQRCode.objects.get(qr_code_id=qr_code_id, is_active=True)
        except PixQRCode.DoesNotExist:
            raise forms.ValidationError('QR Code não encontrado ou inativo')
        
        if self.qr_code.is_expired():
            raise forms.ValidationError('QR Code expirado')
        
        if self.qr_code.account == self.account:
            raise forms.ValidationError('Não é possível pagar seu próprio QR Code')
        
        return qr_code_id

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        
        if hasattr(self, 'qr_code'):
            if self.qr_code.amount:
                cleaned_data['amount'] = self.qr_code.amount
            elif not amount:
                raise forms.ValidationError('Valor é obrigatório para QR Code com valor variável')
            
            final_amount = cleaned_data.get('amount')
            if final_amount and self.account.balance < final_amount:
                raise forms.ValidationError(
                    f'Saldo insuficiente. Saldo disponível: ${self.account.balance}'
                )
        
        return cleaned_data
