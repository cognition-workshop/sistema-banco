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
    destination_account_no = forms.IntegerField(
        label='Destination Account Number',
        min_value=1
    )

    class Meta(TransactionForm.Meta):
        fields = TransactionForm.Meta.fields + ['destination_account_no']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destination_account_no'].widget.attrs.update({
            'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight border rounded-md border-gray-500 focus:outline-none focus:shadow-outline',
            'placeholder': 'Enter destination account number'
        })

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount <= 0:
            raise forms.ValidationError('Transfer amount must be positive')
        
        if amount > self.account.balance:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {self.account.balance}$'
            )
        
        return amount

    def clean_destination_account_no(self):
        from accounts.models import UserBankAccount
        
        destination_account_no = self.cleaned_data.get('destination_account_no')
        
        if not UserBankAccount.objects.filter(account_no=destination_account_no).exists():
            raise forms.ValidationError('Destination account does not exist')
        
        if destination_account_no == self.account.account_no:
            raise forms.ValidationError('Cannot transfer to your own account')
        
        return destination_account_no


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
