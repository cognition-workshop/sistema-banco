from django.contrib import admin
from .models import BankAccountType, User, UserAddress, UserBankAccount
from transactions.models import PIXKey


class PIXKeyInline(admin.TabularInline):
    model = PIXKey
    extra = 0
    readonly_fields = ['created_at']
    fields = ['key_type', 'key_value', 'is_active', 'created_at']


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'get_formatted_cpf_display', 'first_name', 'last_name', 'is_active']
    list_filter = ['is_active', 'is_staff', 'gender']
    search_fields = ['email', 'cpf', 'first_name', 'last_name']
    readonly_fields = ['date_joined']
    inlines = [PIXKeyInline]
    
    def get_formatted_cpf_display(self, obj):
        return obj.get_formatted_cpf()
    get_formatted_cpf_display.short_description = 'CPF'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address_line_1', 'city', 'state', 'zip_code']
    search_fields = ['user__email', 'user__cpf', 'city', 'state']
    list_filter = ['state']


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_formatted_account_display', 'account_type', 'balance']
    search_fields = ['user__email', 'user__cpf', 'account_no']
    list_filter = ['account_type']
    readonly_fields = ['balance']
    
    def get_formatted_account_display(self, obj):
        return obj.get_formatted_account()
    get_formatted_account_display.short_description = 'Conta'
