import datetime

from django import forms
from django.conf import settings
from django.utils import timezone
import pytz

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


class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")

        try:
            daterange = daterange.split(' - ')
            if len(daterange) == 2:
                tz = pytz.timezone(settings.TIME_ZONE)
                dates = []
                for date_str in daterange:
                    naive_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    aware_datetime = tz.localize(naive_date)
                    dates.append(aware_datetime.date())
                return dates
            else:
                raise forms.ValidationError("Please select a date range.")
        except (ValueError, AttributeError):
            raise forms.ValidationError("Invalid date range")
