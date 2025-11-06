from django.contrib import admin
from django.urls import path

from .models import BankAccountType, User, UserAddress, UserBankAccount
from .views import system_health_dashboard


class CustomAdminSite(admin.AdminSite):
    site_header = 'Banking System Administration'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('system-health/', system_health_dashboard, name='system_health_dashboard'),
        ]
        return custom_urls + urls


admin_site = CustomAdminSite(name='admin')

admin_site.register(BankAccountType)
admin_site.register(User)
admin_site.register(UserAddress)
admin_site.register(UserBankAccount)
