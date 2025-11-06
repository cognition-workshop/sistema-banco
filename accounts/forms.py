import datetime
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction, IntegrityError, DatabaseError
import logging

from .models import User, BankAccountType, UserBankAccount, UserAddress
from .constants import GENDER_CHOICE
from .validators import (
    validate_name_format, validate_minimum_age,
    validate_postal_code_format, validate_allowed_address_chars, VALID_COUNTRIES
)

logger = logging.getLogger(__name__)


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
        
        self.fields['street_address'].widget.attrs.update({
            'maxlength': '512',
            'required': 'required'
        })
        self.fields['city'].widget.attrs.update({
            'maxlength': '256',
            'required': 'required'
        })
        self.fields['postal_code'].widget.attrs.update({
            'pattern': r'\d{5}-?\d{3}',
            'title': 'Formato: XXXXX-XXX ou XXXXXXXX',
            'placeholder': '00000-000',
            'maxlength': '9',
            'required': 'required'
        })
        self.fields['country'].widget.attrs.update({
            'maxlength': '256',
            'required': 'required'
        })

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code:
            validate_postal_code_format(postal_code)
        return postal_code

    def clean_street_address(self):
        street_address = self.cleaned_data.get('street_address')
        if street_address:
            validate_allowed_address_chars(street_address)
        return street_address

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if city:
            validate_allowed_address_chars(city)
        return city

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if country and country not in VALID_COUNTRIES:
            raise forms.ValidationError(
                f'País inválido. Países aceitos: {", ".join(VALID_COUNTRIES[:5])}...'
            )
        return country


class UserRegistrationForm(UserCreationForm):
    account_type = forms.ModelChoiceField(
        queryset=BankAccountType.objects.all()
    )
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    birth_date = forms.DateField()

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
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
        
        self.fields['first_name'].widget.attrs.update({
            'pattern': r'[A-Za-zÀ-ÿ\s]+',
            'title': 'Apenas letras e espaços',
            'minlength': '2',
            'maxlength': '150',
            'required': 'required'
        })
        self.fields['last_name'].widget.attrs.update({
            'pattern': r'[A-Za-zÀ-ÿ\s]+',
            'title': 'Apenas letras e espaços',
            'minlength': '2',
            'maxlength': '150',
            'required': 'required'
        })
        self.fields['email'].widget.attrs.update({
            'type': 'email',
            'required': 'required'
        })
        self.fields['birth_date'].widget.attrs.update({
            'type': 'date',
            'max': datetime.date.today().isoformat(),
            'required': 'required'
        })
        self.fields['password1'].widget.attrs.update({
            'minlength': '8',
            'required': 'required'
        })
        self.fields['password2'].widget.attrs.update({
            'minlength': '8',
            'required': 'required'
        })

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            validate_name_format(first_name)
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            validate_name_format(last_name)
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Este email já está cadastrado. Por favor, use outro email.'
            )
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            validate_minimum_age(birth_date)
        return birth_date

    @transaction.atomic
    def save(self, commit=True):
        try:
            user = super().save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            if commit:
                user.save()
                account_type = self.cleaned_data.get('account_type')
                gender = self.cleaned_data.get('gender')
                birth_date = self.cleaned_data.get('birth_date')

                UserBankAccount.objects.create(
                    user=user,
                    gender=gender,
                    birth_date=birth_date,
                    account_type=account_type,
                    account_no=(
                        user.id +
                        settings.ACCOUNT_NUMBER_START_FROM
                    )
                )
                
                logger.info(
                    f'Conta bancária criada para usuário: {user.email}'
                )
            return user
        except (IntegrityError, DatabaseError) as e:
            logger.error(
                f'Erro ao salvar usuário no formulário de registro. '
                f'Erro: {str(e)}',
                exc_info=True
            )
            raise
