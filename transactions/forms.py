import datetime

from django import forms
from django.conf import settings
from django.db import transaction

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
    account_no = forms.IntegerField(
        label='Recipient Account Number',
        help_text='Enter the account number to transfer to'
    )

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        account_no = cleaned_data.get('account_no')
        
        if not amount or not account_no:
            return cleaned_data
        
        if amount <= 0:
            raise forms.ValidationError('Transfer amount must be positive')
        
        from accounts.models import UserBankAccount
        try:
            recipient_account = UserBankAccount.objects.get(account_no=account_no)
            cleaned_data['recipient_account'] = recipient_account
        except UserBankAccount.DoesNotExist:
            raise forms.ValidationError(
                f'Account number {account_no} does not exist'
            )
        
        if self.account.account_no == account_no:
            raise forms.ValidationError(
                'Cannot transfer to your own account'
            )
        
        if self.account.balance < amount:
            raise forms.ValidationError(
                f'Insufficient balance. Your current balance is {self.account.balance} $'
            )
        
        return cleaned_data
    
    @transaction.atomic
    def save(self, commit=True):
        if not commit:
            return None
        
        amount = self.cleaned_data.get('amount')
        recipient_account = self.cleaned_data.get('recipient_account')
        sender_account = self.account
        
        sender_account.balance -= amount
        sender_account.save(update_fields=['balance'])
        
        recipient_account.balance += amount
        recipient_account.save(update_fields=['balance'])
        
        Transaction.objects.create(
            account=sender_account,
            amount=-amount,
            balance_after_transaction=sender_account.balance,
            transaction_type=self.cleaned_data.get('transaction_type')
        )
        
        Transaction.objects.create(
            account=recipient_account,
            amount=amount,
            balance_after_transaction=recipient_account.balance,
            transaction_type=self.cleaned_data.get('transaction_type')
        )
        
        return None


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
