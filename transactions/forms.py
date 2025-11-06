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

        if amount > balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {balance} $'
            )

        return amount


class TransferForm(TransactionForm):
    recipient_account_number = forms.IntegerField(
        label='Recipient Account Number',
        help_text='Enter the account number of the recipient'
    )

    def clean_recipient_account_number(self):
        from accounts.models import UserBankAccount
        recipient_account_number = self.cleaned_data.get('recipient_account_number')
        
        try:
            recipient_account = UserBankAccount.objects.get(
                account_no=recipient_account_number
            )
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError(
                f'Account number {recipient_account_number} does not exist'
            )
        
        if recipient_account == self.account:
            raise forms.ValidationError(
                'You cannot transfer money to your own account'
            )
        
        return recipient_account_number

    def clean_amount(self):
        min_transfer_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        balance = self.account.balance
        amount = self.cleaned_data.get('amount')

        if amount < min_transfer_amount:
            raise forms.ValidationError(
                f'You can transfer at least {min_transfer_amount} $'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {balance} $'
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
