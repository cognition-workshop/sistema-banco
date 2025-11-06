import datetime
import hashlib

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
        
        if self.request:
            self.instance.ip_address = getattr(self.request, 'client_ip', 'unknown')
            self.instance.geolocation = self._get_geolocation(self.instance.ip_address)
            self.instance.channel = self._get_channel(self.request)
        else:
            self.instance.ip_address = 'system'
            self.instance.geolocation = 'N/A'
            self.instance.channel = 'system'
        
        self.instance.hash_signature = self._generate_hash()
        
        return super().save()
    
    def _get_geolocation(self, ip_address):
        return 'Unknown' if ip_address == 'unknown' else ip_address
    
    def _get_channel(self, request):
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return 'api'
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        return 'web'
    
    def _generate_hash(self):
        data = f"{self.instance.account.account_no}{self.instance.amount}{self.instance.transaction_type}{self.instance.ip_address}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def log_failed_transaction(self, failure_reason):
        from .models import FailedTransaction
        
        failed_trans = FailedTransaction(
            account=self.account,
            attempted_amount=self.cleaned_data.get('amount', 0),
            attempted_transaction_type=self.data.get('transaction_type') or self.initial.get('transaction_type'),
            failure_reason=failure_reason,
        )
        
        if self.request:
            failed_trans.ip_address = getattr(self.request, 'client_ip', 'unknown')
            failed_trans.geolocation = self._get_geolocation(failed_trans.ip_address)
            failed_trans.channel = self._get_channel(self.request)
            failed_trans.hash_signature = hashlib.sha256(f"{self.account.account_no}{failure_reason}".encode()).hexdigest()
        
        failed_trans.save()


class DepositForm(TransactionForm):

    def clean_amount(self):
        min_deposit_amount = settings.MINIMUM_DEPOSIT_AMOUNT
        amount = self.cleaned_data.get('amount')

        if amount < min_deposit_amount:
            error_msg = f'You need to deposit at least {min_deposit_amount} $'
            self.log_failed_transaction(error_msg)
            raise forms.ValidationError(error_msg)

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
            error_msg = f'You can withdraw at least {min_withdraw_amount} $'
            self.log_failed_transaction(error_msg)
            raise forms.ValidationError(error_msg)

        if amount > max_withdraw_amount:
            error_msg = f'You can withdraw at most {max_withdraw_amount} $'
            self.log_failed_transaction(error_msg)
            raise forms.ValidationError(error_msg)

        if amount > balance:
            error_msg = f'Insufficient balance. Your balance is {balance} $'
            self.log_failed_transaction(error_msg)
            raise forms.ValidationError(error_msg)

        return amount


class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")
        
        if not daterange:
            return None
        
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


class IRPFYearForm(forms.Form):
    year = forms.IntegerField(
        required=False,
        widget=forms.Select(choices=[]),
        label='Ano'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        current_year = timezone.now().year
        year_choices = [(year, str(year)) for year in range(2020, current_year + 1)]
        year_choices.insert(0, ('', 'Selecione o ano'))
        self.fields['year'].widget.choices = year_choices
