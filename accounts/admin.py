from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'annual_interest_rate', 'interest_calculation_per_year', 'maximum_withdrawal_amount']
    list_filter = ['interest_calculation_per_year']
    search_fields = ['name']


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user_email', 'account_type', 'balance_display', 'gender', 'birth_date']
    list_filter = ['account_type', 'gender']
    search_fields = ['account_no', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_no', 'balance', 'initial_deposit_date', 'interest_start_date']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def balance_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">R$ {}</span>',
            'green' if obj.balance >= 0 else 'red',
            f'{obj.balance:,.2f}'
        )
    balance_display.short_description = 'Saldo'
    balance_display.admin_order_field = 'balance'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'city', 'country', 'postal_code']
    list_filter = ['country', 'city']
    search_fields = ['user__email', 'city', 'street_address', 'postal_code']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
