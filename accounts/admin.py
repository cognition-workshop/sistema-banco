from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import BankAccountType, User, UserAddress, UserBankAccount
from transactions.models import Transaction


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    extra = 0
    readonly_fields = ('account_no', 'balance')
    can_delete = False


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    extra = 0
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'get_full_name', 'get_account_number', 
        'get_account_type', 'get_balance', 'date_joined', 'is_active'
    )
    list_filter = (
        'is_active', 'is_staff', 'date_joined',
        'account__account_type',
    )
    search_fields = ('email', 'first_name', 'last_name', 'account__account_no')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    inlines = [UserBankAccountInline, UserAddressInline]
    readonly_fields = ('date_joined', 'last_login')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'
    
    def get_account_number(self, obj):
        return obj.account.account_no if hasattr(obj, 'account') else 'N/A'
    get_account_number.short_description = 'Account Number'
    get_account_number.admin_order_field = 'account__account_no'
    
    def get_account_type(self, obj):
        return obj.account.account_type.name if hasattr(obj, 'account') else 'N/A'
    get_account_type.short_description = 'Account Type'
    get_account_type.admin_order_field = 'account__account_type__name'
    
    def get_balance(self, obj):
        if hasattr(obj, 'account'):
            return format_html('<strong>${:,.2f}</strong>', obj.account.balance)
        return 'N/A'
    get_balance.short_description = 'Balance'
    get_balance.admin_order_field = 'account__balance'


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('amount', 'balance_after_transaction', 'transaction_type', 'timestamp')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_no', 'get_user_email', 'account_type', 
        'balance', 'initial_deposit_date', 'get_transaction_count'
    )
    list_filter = ('account_type', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('account_no', 'balance', 'initial_deposit_date', 'interest_start_date')
    
    inlines = [TransactionInline]
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_type', 'account_no', 'balance')
        }),
        ('Personal Information', {
            'fields': ('gender', 'birth_date')
        }),
        ('Dates', {
            'fields': ('initial_deposit_date', 'interest_start_date')
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_transaction_count(self, obj):
        return obj.transactions.count()
    get_transaction_count.short_description = 'Total Transactions'


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'maximum_withdrawal_amount', 'annual_interest_rate',
        'interest_calculation_per_year', 'get_account_count'
    )
    list_filter = ('interest_calculation_per_year',)
    search_fields = ('name',)
    
    def get_account_count(self, obj):
        return obj.accounts.count()
    get_account_count.short_description = 'Number of Accounts'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('get_user_email', 'city', 'country', 'postal_code')
    list_filter = ('country', 'city')
    search_fields = ('user__email', 'city', 'country', 'street_address')
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
