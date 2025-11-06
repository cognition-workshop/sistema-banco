from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import User, BankAccountType, UserBankAccount, UserAddress
from .constants import GENDER_CHOICE


class UserAddressForm(forms.ModelForm):

    class Meta:
        model = UserAddress
        fields = ["street_address", "city", "postal_code", "country"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "appearance-none block w-full bg-gray-200 "
                        "text-gray-700 border border-gray-200 rounded "
                        "py-3 px-4 leading-tight focus:outline-none "
                        "focus:bg-white focus:border-gray-500"
                    )
                }
            )


class UserRegistrationForm(UserCreationForm):
    account_type = forms.ModelChoiceField(queryset=BankAccountType.objects.all())
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    birth_date = forms.DateField()

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "appearance-none block w-full bg-gray-200 "
                        "text-gray-700 border border-gray-200 "
                        "rounded py-3 px-4 leading-tight "
                        "focus:outline-none focus:bg-white "
                        "focus:border-gray-500"
                    )
                }
            )

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name or len(first_name) < 2:
            raise forms.ValidationError("O nome deve ter pelo menos 2 caracteres")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not last_name or len(last_name) < 2:
            raise forms.ValidationError("O sobrenome deve ter pelo menos 2 caracteres")
        return last_name

    def clean_birth_date(self):
        from datetime import date

        birth_date = self.cleaned_data.get("birth_date")
        if birth_date:
            today = date.today()
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
            if age < 18:
                raise forms.ValidationError(
                    "Você deve ter pelo menos 18 anos para abrir uma conta"
                )
            if age > 120:
                raise forms.ValidationError("Data de nascimento inválida")
        return birth_date

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            account_type = self.cleaned_data.get("account_type")
            gender = self.cleaned_data.get("gender")
            birth_date = self.cleaned_data.get("birth_date")

            UserBankAccount.objects.create(
                user=user,
                gender=gender,
                birth_date=birth_date,
                account_type=account_type,
                account_no=(user.id + settings.ACCOUNT_NUMBER_START_FROM),
            )
        return user
