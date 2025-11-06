import datetime

from django import forms
from django.conf import settings

from .models import Transaction
from accounts.models import UserBankAccount


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

        if amount > balance:
            raise forms.ValidationError('Insufficient funds')

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


class TransferForm(forms.Form):
    recipient_account_no = forms.IntegerField(label='Recipient Account Number')
    amount = forms.DecimalField(decimal_places=2, max_digits=12)

    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('sender_account')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get('amount')
        recipient_no = cleaned.get('recipient_account_no')

        if amount is None or amount <= 0:
            raise forms.ValidationError('Transfer amount must be positive')

        if recipient_no is None:
            raise forms.ValidationError('Recipient account is required')

        try:
            recipient = UserBankAccount.objects.get(account_no=recipient_no)
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError('Recipient account does not exist')

        if recipient.pk == self.sender_account.pk:
            raise forms.ValidationError('Cannot transfer to the same account')

        if amount > self.sender_account.balance:
            raise forms.ValidationError('Insufficient funds')

        cleaned['recipient'] = recipient
        return cleaned
