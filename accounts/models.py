from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models

from .constants import GENDER_CHOICE
from .managers import UserManager


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
    agency = models.CharField(
        max_length=4,
        help_text='Agência bancária (4 dígitos)'
    )
    account_number = models.CharField(
        max_length=7,
        help_text='Número da conta (7 dígitos)'
    )
    check_digit = models.CharField(
        max_length=1,
        help_text='Dígito verificador (1 dígito)'
    )
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
        from .utils import format_account
        return format_account(self.agency, self.account_number, self.check_digit)

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
    
    def get_formatted_account(self):
        """Returns account in format AAAA-CCCCCCC-D"""
        from .utils import format_account
        return format_account(self.agency, self.account_number, self.check_digit)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from .utils import validate_dac10
        
        errors = {}
        
        if self.agency and not self.agency.isdigit():
            errors['agency'] = 'Agência deve conter apenas dígitos.'
        elif self.agency and len(self.agency) != 4:
            errors['agency'] = 'Agência deve ter exatamente 4 dígitos.'
        
        if self.account_number and not self.account_number.isdigit():
            errors['account_number'] = 'Número da conta deve conter apenas dígitos.'
        elif self.account_number and len(self.account_number) != 7:
            errors['account_number'] = 'Número da conta deve ter exatamente 7 dígitos.'
        
        if self.check_digit and not self.check_digit.isdigit():
            errors['check_digit'] = 'Dígito verificador deve ser um dígito.'
        elif self.check_digit and len(self.check_digit) != 1:
            errors['check_digit'] = 'Dígito verificador deve ter exatamente 1 dígito.'
        elif self.agency and self.account_number and self.check_digit:
            if not validate_dac10(self.agency, self.account_number, self.check_digit):
                errors['check_digit'] = 'Dígito verificador inválido.'
        
        if errors:
            raise ValidationError(errors)


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
