from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'annual_interest_rate', 'maximum_withdrawal_amount']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country']


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['get_account_number', 'cpf', 'user', 'balance', 'account_type']
    search_fields = ['cpf', 'user__email']
    readonly_fields = ['get_account_number']
