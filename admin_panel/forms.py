from django import forms
from django.contrib.auth import get_user_model
from transactions.constants import TRANSACTION_TYPE_CHOICES
from .models import FraudAlert

User = get_user_model()


class UserSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search by email or name',
        'class': 'w-full px-4 py-2 border rounded-md'
    }))
    status = forms.ChoiceField(required=False, choices=[
        ('', 'All Status'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], widget=forms.Select(attrs={'class': 'px-4 py-2 border rounded-md'}))


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md'}),
        }


class TransactionFilterForm(forms.Form):
    user_email = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'User email',
        'class': 'px-4 py-2 border rounded-md'
    }))
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(TRANSACTION_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'px-4 py-2 border rounded-md'})
    )
    min_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Min amount',
        'class': 'px-4 py-2 border rounded-md'
    }))
    max_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={
        'placeholder': 'Max amount',
        'class': 'px-4 py-2 border rounded-md'
    }))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'px-4 py-2 border rounded-md'
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'px-4 py-2 border rounded-md'
    }))


class DateRangeForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'px-4 py-2 border rounded-md'
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'px-4 py-2 border rounded-md'
    }))


class FraudAlertReviewForm(forms.ModelForm):
    class Meta:
        model = FraudAlert
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'px-4 py-2 border rounded-md'}),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-2 border rounded-md'
            }),
        }
