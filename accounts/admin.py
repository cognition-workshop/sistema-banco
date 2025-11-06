from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BankAccountType, User, UserAddress, UserBankAccount
from transactions.models import Transaction


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    can_delete = False
    verbose_name_plural = 'Bank Account'
    fk_name = 'user'
    fields = ('account_type', 'account_no', 'gender', 'birth_date', 'balance', 'initial_deposit_date', 'interest_start_date')
    readonly_fields = ('account_no', 'balance')


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    can_delete = False
    verbose_name_plural = 'Address'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'get_full_name', 'get_account_no', 'get_account_type', 'get_balance', 'date_joined', 'is_active')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'account__account_type')
    search_fields = ('email', 'first_name', 'last_name', 'account__account_no')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    inlines = [UserBankAccountInline, UserAddressInline]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else "-"
    get_full_name.short_description = 'Full Name'
    
    def get_account_no(self, obj):
        return obj.account.account_no if hasattr(obj, 'account') else "-"
    get_account_no.short_description = 'Account Number'
    get_account_no.admin_order_field = 'account__account_no'
    
    def get_account_type(self, obj):
        return obj.account.account_type.name if hasattr(obj, 'account') else "-"
    get_account_type.short_description = 'Account Type'
    get_account_type.admin_order_field = 'account__account_type'
    
    def get_balance(self, obj):
        return f"${obj.balance:.2f}" if hasattr(obj, 'account') else "-"
    get_balance.short_description = 'Balance'
    get_balance.admin_order_field = 'account__balance'


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('amount', 'transaction_type', 'balance_after_transaction', 'timestamp')
    fields = ('timestamp', 'transaction_type', 'amount', 'balance_after_transaction')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user', 'account_type', 'balance', 'gender', 'birth_date', 'initial_deposit_date')
    list_filter = ('account_type', 'gender', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('account_no',)
    ordering = ('-initial_deposit_date',)
    
    inlines = [TransactionInline]
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_no', 'account_type', 'balance')
        }),
        ('Personal Information', {
            'fields': ('gender', 'birth_date')
        }),
        ('Dates', {
            'fields': ('initial_deposit_date', 'interest_start_date')
        }),
    )


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year')
    list_filter = ('interest_calculation_per_year',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street_address', 'city', 'postal_code', 'country')
    list_filter = ('country', 'city')
    search_fields = ('user__email', 'street_address', 'city', 'country')
    ordering = ('user__email',)
