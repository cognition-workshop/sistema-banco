from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import BankAccountType, User, UserAddress, UserBankAccount


admin.site.site_header = "Banking System Administration"
admin.site.site_title = "Banking Admin"
admin.site.index_title = "Welcome to Banking System Admin Portal"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'account_number', 'balance_display', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'account__account_no']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    actions = ['suspend_users', 'activate_users']
    
    def account_number(self, obj):
        if hasattr(obj, 'account'):
            url = reverse('admin:accounts_userbankaccount_change', args=[obj.account.id])
            return format_html('<a href="{}">{}</a>', url, obj.account.account_no)
        return '-'
    account_number.short_description = 'Account Number'
    
    def balance_display(self, obj):
        balance = obj.balance
        color = 'green' if balance > 0 else 'red' if balance < 0 else 'black'
        return format_html('<span style="color: {};">${}</span>', color, f'{balance:.2f}')
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'account__balance'
    
    @admin.action(description='Suspend selected users')
    def suspend_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) suspended successfully.')
    
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year', 'total_accounts']
    search_fields = ['name']
    ordering = ['name']
    
    def total_accounts(self, obj):
        return obj.accounts.count()
    total_accounts.short_description = 'Total Accounts'


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user_link', 'account_type', 'balance_display', 'gender', 'birth_date', 'initial_deposit_date']
    list_filter = ['account_type', 'gender', 'initial_deposit_date']
    search_fields = ['account_no', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_no']
    ordering = ['-initial_deposit_date']
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'
    
    def balance_display(self, obj):
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'black'
        return format_html('<span style="color: {};">${}</span>', color, f'{obj.balance:.2f}')
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'balance'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'street_address', 'city', 'postal_code', 'country']
    list_filter = ['country', 'city']
    search_fields = ['user__email', 'street_address', 'city', 'country']
    
    def user_email(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_email.short_description = 'User'
