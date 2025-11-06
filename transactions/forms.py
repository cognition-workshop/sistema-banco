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
        
        self.balance_before_transaction = self.account.balance

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def _get_client_ip(self):
        if not self.request:
            return None
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        self.instance.balance_before_transaction = self.balance_before_transaction
        
        if self.request:
            self.instance.performed_by = getattr(self.request, 'user', None)
            if self.instance.performed_by and not self.instance.performed_by.is_authenticated:
                self.instance.performed_by = None
            self.instance.ip_address = self._get_client_ip()
            self.instance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:500]
            self.instance.operation_source = 'web'
        
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
