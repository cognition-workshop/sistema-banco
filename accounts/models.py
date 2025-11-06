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
    """
    Validates Brazilian CPF number using check digits algorithm.
    Expected format: ###.###.###-## or ###########
    """
    cpf = ''.join(filter(str.isdigit, value))
    
    if len(cpf) != 11:
        raise ValidationError('CPF deve conter 11 dígitos')
    
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido')
    
    def calculate_digit(cpf_partial):
        total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, range(len(cpf_partial) + 1, 1, -1)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_digit = calculate_digit(cpf[:9])
    second_digit = calculate_digit(cpf[:10])
    
    if cpf[9] != str(first_digit) or cpf[10] != str(second_digit):
        raise ValidationError('CPF inválido')
    
    return value


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[validate_cpf],
        help_text='CPF no formato ###.###.###-##'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def get_formatted_cpf(self):
        """Returns CPF in formatted ###.###.###-## format"""
        cpf_digits = ''.join(filter(str.isdigit, self.cpf))
        return f'{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}'

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
    bank_code = models.CharField(max_length=3, default='237')
    branch_code = models.CharField(max_length=4)
    account_no = models.PositiveIntegerField(unique=True)
    account_check_digit = models.CharField(max_length=2)
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
        return self.get_formatted_account()
    
    def get_formatted_account(self):
        """Returns account in Brazilian format: ####-#-######-#"""
        return f'{self.branch_code}-{self.bank_code[-1]}-{str(self.account_no).zfill(6)}-{self.account_check_digit}'

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
