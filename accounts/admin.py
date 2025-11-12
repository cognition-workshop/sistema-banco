from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_admin', 'role', 'is_staff', 'is_active')
    list_filter = ('is_admin', 'role', 'is_staff', 'is_superuser', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'role', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_admin', 'role'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')
    
    actions = ['assign_admin_role', 'assign_supervisor_role', 'assign_auditor_role']
    
    def assign_admin_role(self, request, queryset):
        queryset.update(is_admin=True, role='admin')
        self.message_user(request, f"{queryset.count()} users assigned Admin role.")
    assign_admin_role.short_description = "Assign Admin role to selected users"
    
    def assign_supervisor_role(self, request, queryset):
        queryset.update(is_admin=True, role='supervisor')
        self.message_user(request, f"{queryset.count()} users assigned Supervisor role.")
    assign_supervisor_role.short_description = "Assign Supervisor role to selected users"
    
    def assign_auditor_role(self, request, queryset):
        queryset.update(is_admin=True, role='auditor')
        self.message_user(request, f"{queryset.count()} users assigned Auditor role.")
    assign_auditor_role.short_description = "Assign Auditor role to selected users"


admin.site.register(User, UserAdmin)
admin.site.register(BankAccountType)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount)
