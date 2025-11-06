import re
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
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

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get("postal_code")
        if postal_code:
            postal_str = str(postal_code)
            if len(postal_str) != 8:
                raise ValidationError("Postal code must be exactly 8 digits.")
            if not postal_str.isdigit():
                raise ValidationError("Postal code must contain only numbers.")
        return postal_code

    def clean_street_address(self):
        street = self.cleaned_data.get("street_address")
        if street:
            if len(street) < 5:
                raise ValidationError("Street address is too short.")
        return street


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

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_regex, email):
                raise ValidationError("Please enter a valid email address.")
            if User.objects.filter(email=email).exists():
                raise ValidationError("This email is already registered.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if password:
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", password):
                raise ValidationError(
                    "Password must contain at least one uppercase letter."
                )
            if not re.search(r"[a-z]", password):
                raise ValidationError(
                    "Password must contain at least one lowercase letter."
                )
            if not re.search(r"\d", password):
                raise ValidationError("Password must contain at least one number.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                raise ValidationError(
                    "Password must contain at least one special character."
                )
        return password

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
