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
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):

    def clean_amount(self):
        from .audit import create_audit_log
        from .constants import DEPOSIT_ATTEMPT
        
        min_deposit_amount = settings.MINIMUM_DEPOSIT_AMOUNT
        amount = self.cleaned_data.get('amount')

        if amount < min_deposit_amount:
            error_msg = f'You need to deposit at least {min_deposit_amount} $'
            create_audit_log(
                action_type=DEPOSIT_ATTEMPT,
                success=False,
                amount=amount,
                error_message=error_msg,
                request=self.request,
                additional_data={'min_required': float(min_deposit_amount)}
            )
            raise forms.ValidationError(error_msg)

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        from .audit import create_audit_log
        from .constants import WITHDRAW_ATTEMPT
        
        account = self.account
        min_withdraw_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        max_withdraw_amount = (
            account.account_type.maximum_withdrawal_amount
        )
        balance = account.balance

        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            error_msg = f'You can withdraw at least {min_withdraw_amount} $'
            create_audit_log(
                action_type=WITHDRAW_ATTEMPT,
                success=False,
                amount=amount,
                error_message=error_msg,
                request=self.request,
                additional_data={'min_required': float(min_withdraw_amount)}
            )
            raise forms.ValidationError(error_msg)

        if amount > max_withdraw_amount:
            error_msg = f'You can withdraw at most {max_withdraw_amount} $'
            create_audit_log(
                action_type=WITHDRAW_ATTEMPT,
                success=False,
                amount=amount,
                error_message=error_msg,
                request=self.request,
                additional_data={'max_allowed': float(max_withdraw_amount)}
            )
            raise forms.ValidationError(error_msg)

        if amount > balance:
            error_msg = f'Insufficient balance. Your balance is {balance} $'
            create_audit_log(
                action_type=WITHDRAW_ATTEMPT,
                success=False,
                amount=amount,
                error_message=error_msg,
                request=self.request,
                additional_data={'balance': float(balance)}
            )
            raise forms.ValidationError(error_msg)

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
