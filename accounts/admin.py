from django.contrib import admin, messages

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    extra = 0
    readonly_fields = ['account_no', 'initial_deposit_date']
    can_delete = False


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    extra = 0
    can_delete = False


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    inlines = [UserBankAccountInline, UserAddressInline]


class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'user', 'balance', 'account_type', 'initial_deposit_date']
    list_filter = ['account_type', 'initial_deposit_date']
    search_fields = ['account_no', 'user__email']
    readonly_fields = ['account_no', 'initial_deposit_date']
    actions = ['activate_accounts', 'deactivate_accounts']
    
    def save_model(self, request, obj, form, change):
        if change and 'balance' in form.changed_data:
            old_instance = UserBankAccount.objects.get(pk=obj.pk)
            old_balance = old_instance.balance
            new_balance = obj.balance
            
            difference = new_balance - old_balance
            
            super().save_model(request, obj, form, change)
            
            from transactions.models import Transaction
            from transactions.constants import DEPOSIT, WITHDRAWAL
            
            if difference != 0:
                transaction_type = DEPOSIT if difference > 0 else WITHDRAWAL
                Transaction.objects.create(
                    account=obj,
                    amount=abs(difference),
                    balance_after_transaction=new_balance,
                    transaction_type=transaction_type
                )
        else:
            super().save_model(request, obj, form, change)
    
    def activate_accounts(self, request, queryset):
        count = 0
        for account in queryset:
            if hasattr(account, 'user'):
                account.user.is_active = True
                account.user.save(update_fields=['is_active'])
                count += 1
        self.message_user(request, f'{count} account(s) activated.', messages.SUCCESS)
    activate_accounts.short_description = "Activate selected accounts"
    
    def deactivate_accounts(self, request, queryset):
        count = 0
        for account in queryset:
            if hasattr(account, 'user'):
                account.user.is_active = False
                account.user.save(update_fields=['is_active'])
                count += 1
        self.message_user(request, f'{count} account(s) deactivated.', messages.SUCCESS)
    deactivate_accounts.short_description = "Deactivate selected accounts"


admin.site.register(BankAccountType)
admin.site.register(User, UserAdmin)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
