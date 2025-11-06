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


class TransferForm(TransactionForm):
    recipient_account_no = forms.IntegerField(
        label='Recipient Account Number',
        min_value=1
    )

    class Meta(TransactionForm.Meta):
        fields = ['amount', 'transaction_type', 'recipient_account_no']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipient_account_no'].widget.attrs.update({
            'placeholder': 'Enter recipient account number'
        })

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        recipient_account_no = cleaned_data.get('recipient_account_no')
        
        if not amount or not recipient_account_no:
            return cleaned_data

        sender_account = self.account
        if amount > sender_account.balance:
            raise forms.ValidationError(
                f'Saldo insuficiente. Seu saldo atual é ${sender_account.balance}'
            )

        from accounts.models import UserBankAccount
        try:
            recipient_account = UserBankAccount.objects.get(
                account_no=recipient_account_no
            )
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError(
                f'Conta destinatária {recipient_account_no} não encontrada'
            )

        if sender_account.account_no == recipient_account_no:
            raise forms.ValidationError(
                'Você não pode transferir para sua própria conta'
            )

        self.recipient_account = recipient_account
        
        return cleaned_data

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_transfer_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        
        if amount < min_transfer_amount:
            raise forms.ValidationError(
                f'O valor mínimo para transferência é ${min_transfer_amount}'
            )
        
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
