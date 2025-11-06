from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.core.exceptions import ValidationError
from django.db import models

from .constants import GENDER_CHOICE
from .managers import UserManager


def validate_cpf(value):
    """Validate Brazilian CPF number using check digits algorithm."""
    cpf = ''.join(filter(str.isdigit, value))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    sum_digits = sum(int(cpf[i]) * (10 - i) for i in range(9))
    first_check = (sum_digits * 10) % 11
    if first_check == 10:
        first_check = 0
    if first_check != int(cpf[9]):
        raise ValidationError('CPF inválido')
    
    sum_digits = sum(int(cpf[i]) * (11 - i) for i in range(10))
    second_check = (sum_digits * 10) % 11
    if second_check == 10:
        second_check = 0
    if second_check != int(cpf[10]):
        raise ValidationError('CPF inválido')


def calculate_account_check_digit(account_number):
    """Calculate check digit for Brazilian bank account using modulo 11."""
    account_str = str(account_number).zfill(7)
    weights = [2, 3, 4, 5, 6, 7, 8]
    sum_digits = sum(int(account_str[i]) * weights[i] for i in range(7))
    remainder = sum_digits % 11
    check_digit = 11 - remainder
    if check_digit >= 10:
        check_digit = 0
    return check_digit


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def balance(self):
        if hasattr(self, 'account'):
            return self.account.balance
        return 0


class BankAccountType(models.Model):
    name = models.CharField(max_length=128)
    maximum_withdrawal_amount = models.DecimalField(
        decimal_places=2,
        max_digits=12
    )
    annual_interest_rate = models.DecimalField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        decimal_places=2,
        max_digits=5,
        help_text='Interest rate from 0 - 100'
    )
    interest_calculation_per_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text='The number of times interest will be calculated per year'
    )

    def __str__(self):
        return self.name

    def calculate_interest(self, principal):
        """
        Calculate interest for each account type.

        This uses a basic interest calculation formula
        """
        p = principal
        r = self.annual_interest_rate
        n = Decimal(self.interest_calculation_per_year)

        # Basic Future Value formula to calculate interest
        interest = (p * (1 + ((r/100) / n))) - p

        return round(interest, 2)


class UserBankAccount(models.Model):
    user = models.OneToOneField(
        User,
        related_name='account',
        on_delete=models.CASCADE,
    )
    account_type = models.ForeignKey(
        BankAccountType,
        related_name='accounts',
        on_delete=models.CASCADE
    )
    account_no = models.PositiveIntegerField(unique=True)
    agencia = models.CharField(max_length=4, default='0001', help_text='Agência (4 dígitos)')
    cpf = models.CharField(max_length=14, unique=True, validators=[validate_cpf], help_text='CPF no formato XXX.XXX.XXX-XX')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    birth_date = models.DateField(null=True, blank=True)
    balance = models.DecimalField(
        default=0,
        max_digits=12,
        decimal_places=2
    )
    interest_start_date = models.DateField(
        null=True, blank=True,
        help_text=(
            'The month number that interest calculation will start from'
        )
    )
    initial_deposit_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.account_no)
    
    @property
    def formatted_account(self):
        """Return account number with check digit in format XXXXXXX-X"""
        check_digit = calculate_account_check_digit(self.account_no)
        return f"{str(self.account_no).zfill(7)}-{check_digit}"

    def get_interest_calculation_months(self):
        """
        List of month numbers for which the interest will be calculated

        returns [2, 4, 6, 8, 10, 12] for every 2 months interval
        """
        interval = int(
            12 / self.account_type.interest_calculation_per_year
        )
        start = self.interest_start_date.month
        return [i for i in range(start, 13, interval)]


class UserAddress(models.Model):
    user = models.OneToOneField(
        User,
        related_name='address',
        on_delete=models.CASCADE,
    )
    street_address = models.CharField(max_length=512)
    city = models.CharField(max_length=256)
    postal_code = models.PositiveIntegerField()
    country = models.CharField(max_length=256)

    def __str__(self):
        return self.user.email
