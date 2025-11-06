from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'maximum_withdrawal_amount', 'annual_interest_rate']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country']
    search_fields = ['user__email', 'city']

@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'cpf', 'agencia', 'conta', 'digito_verificador', 'balance']
    search_fields = ['user__email', 'cpf', 'conta']
    list_filter = ['account_type']
    readonly_fields = ['account_no', 'digito_verificador']
