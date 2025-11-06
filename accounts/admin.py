from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'formatted_account', 'agencia', 'cpf', 'user', 'balance']
    readonly_fields = ['formatted_account']
    search_fields = ['account_no', 'cpf', 'user__email']


admin.site.register(BankAccountType)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
