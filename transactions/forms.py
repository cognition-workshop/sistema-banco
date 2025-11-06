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


class TransferForm(TransactionForm):
    destination_account_no = forms.IntegerField(
        label='Destination Account Number',
        min_value=1
    )

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type',
            'destination_account_no'
        ]

    def clean_destination_account_no(self):
        account_no = self.cleaned_data.get('destination_account_no')
        
        try:
            destination_account = UserBankAccount.objects.get(account_no=account_no)
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError(
                f'Account number {account_no} does not exist'
            )
        
        if destination_account == self.account:
            raise forms.ValidationError(
                'Cannot transfer to the same account'
            )
        
        self.destination_account = destination_account
        return account_no

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_transfer_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        
        if amount < min_transfer_amount:
            raise forms.ValidationError(
                f'You need to transfer at least {min_transfer_amount} $'
            )
        
        if amount > self.account.balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {self.account.balance} $'
            )
        
        return amount
