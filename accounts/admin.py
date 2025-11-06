from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    can_delete = False
    verbose_name_plural = 'Address'
    extra = 0


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    can_delete = False
    verbose_name_plural = 'Bank Account'
    extra = 0
    readonly_fields = ('balance', 'account_no')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'account_status', 'account_balance')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
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
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    inlines = [UserAddressInline, UserBankAccountInline]
    
    actions = ['activate_users', 'deactivate_users']
    
    def account_status(self, obj):
        if hasattr(obj, 'account'):
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No Account</span>'
        )
    account_status.short_description = 'Account Status'
    
    def account_balance(self, obj):
        if hasattr(obj, 'account'):
            return f"${obj.account.balance:,.2f}"
        return "-"
    account_balance.short_description = 'Balance'
    
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user_email', 'account_type', 'balance', 'gender', 'initial_deposit_date')
    list_filter = ('account_type', 'gender', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('balance', 'account_no', 'initial_deposit_date', 'interest_start_date')
    
    fieldsets = (
        ('Account Information', {'fields': ('user', 'account_no', 'account_type', 'balance')}),
        ('Personal Information', {'fields': ('gender', 'birth_date')}),
        ('Interest Information', {'fields': ('initial_deposit_date', 'interest_start_date')}),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'street_address', 'city', 'country', 'postal_code')
    search_fields = ('user__email', 'city', 'country', 'street_address')
    list_filter = ('country', 'city')


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_interest_rate', 'maximum_withdrawal_amount', 'interest_calculation_per_year')
    list_filter = ('interest_calculation_per_year',)
    search_fields = ('name',)
