import datetime

from django import forms
from django.conf import settings

from .models import Transaction


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
                f'Você precisa depositar no mínimo {min_deposit_amount} $'
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
                f'Você pode sacar no mínimo {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'Você pode sacar no máximo {max_withdraw_amount} $'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Seu saldo atual é {balance} $'
            )

        return amount


class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")
        
        if not daterange:
            return None

        try:
            daterange = daterange.split(' - ')
            if len(daterange) != 2:
                raise forms.ValidationError("Por favor, selecione um intervalo de datas.")
            
            start_date = datetime.datetime.strptime(daterange[0], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(daterange[1], '%Y-%m-%d').date()
            
            if start_date > end_date:
                raise forms.ValidationError(
                    "A data inicial deve ser anterior à data final."
                )
            
            today = datetime.date.today()
            if start_date > today or end_date > today:
                raise forms.ValidationError(
                    "Não é possível selecionar datas futuras."
                )
            
            max_days = 365
            days_diff = (end_date - start_date).days
            if days_diff > max_days:
                raise forms.ValidationError(
                    f"O intervalo máximo permitido é de {max_days} dias (1 ano)."
                )
            
            return [start_date, end_date]
        except (ValueError, AttributeError):
            raise forms.ValidationError("Formato de data inválido")
