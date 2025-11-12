from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q

from .models import User, BankAccountType, UserBankAccount, UserAddress
from .constants import GENDER_CHOICE
from .validators import normalize_digits


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

    @transaction.atomic
    def save(self, commit=True):
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
        return user


class UserSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Nome ou E-mail")
    cpf = forms.CharField(required=False, label="CPF")
    status = forms.ChoiceField(
        required=False,
        choices=(("", "Todos"), ("active", "Ativo"), ("suspended", "Suspenso"))
    )
    order_by = forms.ChoiceField(
        required=False,
        choices=(
            ("date_joined", "Data de cadastro"),
            ("first_name", "Nome"),
            ("email", "E-mail"),
            ("cpf", "CPF"),
        ),
        initial="date_joined",
    )
    direction = forms.ChoiceField(
        required=False,
        choices=(("desc", "Desc"), ("asc", "Asc")),
        initial="desc"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-2 px-3 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })

    def cleaned_filters(self):
        q = self.cleaned_data.get("q") or ""
        cpf = normalize_digits(self.cleaned_data.get("cpf") or "")
        status = self.cleaned_data.get("status")
        order_by = self.cleaned_data.get("order_by") or "date_joined"
        direction = self.cleaned_data.get("direction") or "desc"
        return q, cpf, status, order_by, direction

    def apply(self, qs):
        q, cpf, status, order_by, direction = self.cleaned_filters()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q)
            )
        if cpf:
            qs = qs.filter(cpf=cpf)
        if status == "active":
            qs = qs.filter(is_active=True)
        elif status == "suspended":
            qs = qs.filter(is_active=False)
        if direction == "desc":
            order_by = f"-{order_by}"
        return qs.order_by(order_by)


class AdminUserEditForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_staff",
            "is_superuser",
            "groups",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({
                "class": (
                    "appearance-none block w-full bg-gray-200 "
                    "text-gray-700 border border-gray-200 rounded "
                    "py-2 px-3 leading-tight focus:outline-none "
                    "focus:bg-white focus:border-gray-500"
                )
            })
        if self.request and self.instance and self.request.user.pk == self.instance.pk:
            self.fields["is_staff"].disabled = True
            self.fields["is_superuser"].disabled = True
            self.fields["groups"].disabled = True

    def clean(self):
        cleaned = super().clean()
        if self.request and self.instance and self.request.user.pk == self.instance.pk:
            for k in ("is_staff", "is_superuser"):
                if k in self.changed_data:
                    self.add_error(k, "Você não pode alterar suas próprias permissões.")
        return cleaned
