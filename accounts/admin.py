from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_formatted_account', 'account_type', 'balance']
    readonly_fields = ['get_formatted_account']
    
    def get_formatted_account(self, obj):
        return obj.get_formatted_account()
    get_formatted_account.short_description = 'Conta Formatada'


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active']


admin.site.register(BankAccountType)
admin.site.register(User, UserAdmin)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
