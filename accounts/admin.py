from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'account_status']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    actions = ['activate_users', 'deactivate_users']
    
    def account_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    account_status.short_description = 'Status'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user_email', 'account_type', 'balance', 'gender', 'initial_deposit_date']
    list_filter = ['account_type', 'gender', 'initial_deposit_date']
    search_fields = ['account_no', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_no', 'initial_deposit_date', 'interest_start_date']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'city', 'country', 'postal_code']
    list_filter = ['country', 'city']
    search_fields = ['user__email', 'street_address', 'city', 'country']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'annual_interest_rate', 'maximum_withdrawal_amount', 'interest_calculation_per_year']
    list_filter = ['interest_calculation_per_year']
    search_fields = ['name']
