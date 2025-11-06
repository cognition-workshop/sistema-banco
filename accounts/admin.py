from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.contrib.admin.views.decorators import staff_member_required

from .models import BankAccountType, User, UserAddress, UserBankAccount
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


def system_health_dashboard(request):
    total_users = User.objects.count()
    total_accounts = UserBankAccount.objects.count()
    total_balance = UserBankAccount.objects.aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    total_transactions = Transaction.objects.count()
    deposits = Transaction.objects.filter(transaction_type=DEPOSIT).aggregate(
        count=Count('id'),
        total=Sum('amount')
    )
    withdrawals = Transaction.objects.filter(transaction_type=WITHDRAWAL).aggregate(
        count=Count('id'),
        total=Sum('amount')
    )
    interest = Transaction.objects.filter(transaction_type=INTEREST).aggregate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    recent_transactions = Transaction.objects.select_related(
        'account', 'account__user'
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': 'System Health Dashboard',
        'total_users': total_users,
        'total_accounts': total_accounts,
        'total_balance': total_balance,
        'total_transactions': total_transactions,
        'deposits_count': deposits['count'] or 0,
        'deposits_total': deposits['total'] or 0,
        'withdrawals_count': withdrawals['count'] or 0,
        'withdrawals_total': withdrawals['total'] or 0,
        'interest_count': interest['count'] or 0,
        'interest_total': interest['total'] or 0,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'admin/system_health.html', context)


class CustomAdminSite(admin.AdminSite):
    site_header = 'Banking System Administration'
    site_title = 'Banking System Admin'
    index_title = 'System Administration'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('system-health/', self.admin_view(system_health_dashboard), name='system_health'),
        ]
        return custom_urls + urls


admin_site = CustomAdminSite(name='custom_admin')

admin_site.register(BankAccountType)
admin_site.register(User)
admin_site.register(UserAddress)
admin_site.register(UserBankAccount)
