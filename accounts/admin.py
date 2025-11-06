from django.contrib import admin

from .models import BankAccountType, User, UserAddress, UserBankAccount, LoginAttempt


class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'timestamp', 'successful']
    list_filter = ['successful', 'timestamp']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['email', 'ip_address', 'user_agent', 'timestamp', 'successful', 'failure_reason']
    
    def has_add_permission(self, request):
        return False


admin.site.register(BankAccountType)
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserBankAccount)
admin.site.register(LoginAttempt, LoginAttemptAdmin)
