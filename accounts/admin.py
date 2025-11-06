from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'date_joined')
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
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} user(s) activated successfully.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} user(s) deactivated successfully.')
    deactivate_users.short_description = 'Deactivate selected users'


class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user', 'account_type', 'balance', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email')
    list_filter = ('account_type', 'gender')
    ordering = ('-initial_deposit_date',)
    readonly_fields = ('balance',)


admin.site.register(BankAccountType)
admin.site.register(User, UserAdmin)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
