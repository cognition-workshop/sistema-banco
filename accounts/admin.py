from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, Permission
from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informações Pessoais', {'fields': ('email', 'first_name', 'last_name', 'password')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user', 'account_type', 'balance', 'gender', 'initial_deposit_date']
    list_filter = ['account_type', 'gender']
    search_fields = ['account_no', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_no', 'initial_deposit_date', 'interest_start_date']
    
    fieldsets = (
        ('Informações da Conta', {'fields': ('user', 'account_no', 'account_type', 'balance')}),
        ('Informações Pessoais', {'fields': ('gender', 'birth_date')}),
        ('Informações de Juros', {'fields': ('initial_deposit_date', 'interest_start_date')}),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'postal_code']
    search_fields = ['user__email', 'city', 'country', 'street_address']
    list_filter = ['country', 'city']


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year']
    list_filter = ['interest_calculation_per_year']
