from django import forms
from django.contrib.auth.forms import AuthenticationForm
from accounts.models import User, UserBankAccount
from .models import FraudAlert


class AdminLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500',
            'placeholder': 'Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-500',
            'placeholder': 'Password'
        })
    )


class UserSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white',
        'placeholder': 'Search by email or account number'
    }))
    account_status = forms.ChoiceField(required=False, choices=[
        ('', 'All Status'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Verification'),
        ('high_risk', 'High Risk'),
    ], widget=forms.Select(attrs={
        'class': 'block w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 rounded leading-tight focus:outline-none focus:bg-white'
    }))
    balance_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white',
        'placeholder': 'Min Balance'
    }))
    balance_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white',
        'placeholder': 'Max Balance'
    }))


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white'}),
            'last_name': forms.TextInput(attrs={'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white'}),
            'email': forms.EmailInput(attrs={'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white'}),
        }


class TransactionFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white'
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white'
    }))
    transaction_type = forms.ChoiceField(required=False, choices=[
        ('', 'All Types'),
        ('1', 'Deposit'),
        ('2', 'Withdrawal'),
        ('3', 'Interest'),
    ], widget=forms.Select(attrs={
        'class': 'block w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 rounded leading-tight focus:outline-none focus:bg-white'
    }))
    amount_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white',
        'placeholder': 'Min Amount'
    }))
    amount_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white',
        'placeholder': 'Max Amount'
    }))


class FraudAlertForm(forms.ModelForm):
    class Meta:
        model = FraudAlert
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'block w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 rounded leading-tight focus:outline-none focus:bg-white'}),
            'notes': forms.Textarea(attrs={'class': 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white', 'rows': 4}),
        }
