from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import User, BankAccountType, UserBankAccount, UserAddress
from .constants import GENDER_CHOICE


class UserAddressForm(forms.ModelForm):

    class Meta:
        model = UserAddress
        fields = [
            'street_address',
            'city',
            'postal_code',
            'country'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })


class UserRegistrationForm(UserCreationForm):
    account_type = forms.ModelChoiceField(
        queryset=BankAccountType.objects.all()
    )
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    birth_date = forms.DateField()
    cpf = forms.CharField(
        max_length=14,
        help_text='CPF no formato ###.###.###-## ou apenas números'
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'cpf',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 '
                    'rounded py-3 px-4 leading-tight '
                    'focus:outline-none focus:bg-white '
                    'focus:border-gray-500'
                )
            })
    
    def clean_cpf(self):
        """Validate and format CPF"""
        cpf = self.cleaned_data.get('cpf')
        cpf_digits = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_digits) != 11:
            raise forms.ValidationError('CPF deve conter 11 dígitos')
        
        formatted_cpf = f'{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}'
        return formatted_cpf

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            account_type = self.cleaned_data.get('account_type')
            gender = self.cleaned_data.get('gender')
            birth_date = self.cleaned_data.get('birth_date')
            
            account_no = user.id + settings.ACCOUNT_NUMBER_START_FROM
            account_check_digit = str(account_no % 10)

            UserBankAccount.objects.create(
                user=user,
                gender=gender,
                birth_date=birth_date,
                account_type=account_type,
                bank_code=getattr(settings, 'BANK_CODE', '237'),
                branch_code=getattr(settings, 'BRANCH_CODE_DEFAULT', '0001'),
                account_no=account_no,
                account_check_digit=account_check_digit
            )
        return user
