from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
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
    
    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.has_perm('accounts.can_manage_users')
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm('accounts.can_manage_users')


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user', 'account_type', 'balance', 'gender')
    list_filter = ('account_type', 'gender')
    search_fields = ('account_no', 'user__email')
    readonly_fields = ('account_no', 'balance')
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm('accounts.can_view_all_accounts')
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm('accounts.can_manage_users')


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country')
    search_fields = ('user__email', 'city', 'country')


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_interest_rate', 'maximum_withdrawal_amount')
    search_fields = ('name',)
