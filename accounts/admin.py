from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BankAccountType, User, UserAddress, UserBankAccount


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    
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


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user', 'account_type', 'balance', 'gender']
    list_filter = ['account_type', 'gender']
    search_fields = ['account_no', 'user__email']
    readonly_fields = ['account_no', 'balance']
    
    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('accounts.can_manage_users'):
            return self.readonly_fields + ['user', 'account_type']
        return self.readonly_fields
    
    def has_change_permission(self, request, obj=None):
        if not request.user.has_perm('accounts.can_view_all_accounts'):
            return False
        return super().has_change_permission(request, obj)


admin.site.register(BankAccountType)
admin.site.register(UserAddress)
