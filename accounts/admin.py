from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Sum, Count
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from decimal import Decimal

from .models import BankAccountType, User, UserAddress, UserBankAccount, AuditLog


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    can_delete = False
    verbose_name_plural = 'Bank Account'
    fields = ('account_no', 'account_type', 'balance', 'gender', 'birth_date', 
              'interest_start_date', 'initial_deposit_date')
    readonly_fields = ('account_no', 'balance')


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    can_delete = False
    verbose_name_plural = 'Address'
    fields = ('street_address', 'city', 'postal_code', 'country')


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'account_number_display', 
                   'balance_display', 'account_type_display', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 
                   'account__account_type')
    search_fields = ('email', 'first_name', 'last_name', 'account__account_no')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                     'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    inlines = [UserBankAccountInline, UserAddressInline]
    
    @admin.display(description='Account Number', ordering='account__account_no')
    def account_number_display(self, obj):
        if hasattr(obj, 'account'):
            return obj.account.account_no
        return '-'
    
    @admin.display(description='Balance', ordering='account__balance')
    def balance_display(self, obj):
        if hasattr(obj, 'account'):
            balance = obj.account.balance
            color = 'green' if balance > 0 else 'red' if balance < 0 else 'black'
            return format_html(
                '<span style="color: {}; font-weight: bold;">${:,.2f}</span>',
                color, balance
            )
        return '-'
    
    @admin.display(description='Account Type')
    def account_type_display(self, obj):
        if hasattr(obj, 'account'):
            return obj.account.account_type.name
        return '-'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('account', 'account__account_type', 'address')


class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_withdrawal_display', 'interest_rate_display', 
                   'calculation_frequency', 'accounts_count')
    list_filter = ('interest_calculation_per_year',)
    search_fields = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name',)
        }),
        ('Withdrawal Limits', {
            'fields': ('maximum_withdrawal_amount',)
        }),
        ('Interest Configuration', {
            'fields': ('annual_interest_rate', 'interest_calculation_per_year'),
            'description': 'Configure how interest is calculated for this account type'
        }),
    )
    
    @admin.display(description='Max Withdrawal')
    def max_withdrawal_display(self, obj):
        return f'${obj.maximum_withdrawal_amount:,.2f}'
    
    @admin.display(description='Interest Rate')
    def interest_rate_display(self, obj):
        return f'{obj.annual_interest_rate}% annually'
    
    @admin.display(description='Calculation Frequency')
    def calculation_frequency(self, obj):
        return f'{obj.interest_calculation_per_year}x per year'
    
    @admin.display(description='Active Accounts')
    def accounts_count(self, obj):
        return obj.accounts.count()
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('accounts')


class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user_email', 'account_type', 'balance_display', 
                   'gender', 'initial_deposit_date', 'transactions_count')
    list_filter = ('account_type', 'gender', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email', 'user__first_name', 'user__last_name')
    ordering = ('-balance',)
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_no', 'account_type')
        }),
        ('Personal Details', {
            'fields': ('gender', 'birth_date')
        }),
        ('Financial Information', {
            'fields': ('balance', 'initial_deposit_date', 'interest_start_date'),
            'description': 'Balance and interest calculation details'
        }),
    )
    
    readonly_fields = ('account_no', 'balance')
    
    @admin.display(description='User Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    @admin.display(description='Balance', ordering='balance')
    def balance_display(self, obj):
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'black'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:,.2f}</span>',
            color, obj.balance
        )
    
    @admin.display(description='Total Transactions')
    def transactions_count(self, obj):
        return obj.transactions.count()
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'account_type').prefetch_related('transactions')


class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'city', 'country', 'postal_code')
    list_filter = ('country', 'city')
    search_fields = ('user__email', 'city', 'country', 'street_address')
    
    @admin.display(description='User Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


class BankingAdminSite(admin.AdminSite):
    site_header = 'Banking System Administration'
    site_title = 'Banking Admin'
    index_title = 'Dashboard'
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        from django.db.models import Sum, Count, Avg
        from transactions.models import Transaction
        from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
        from datetime import datetime, timedelta
        
        total_users = User.objects.count()
        total_accounts = UserBankAccount.objects.count()
        total_balance = UserBankAccount.objects.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0')
        
        total_transactions = Transaction.objects.count()
        total_deposits = Transaction.objects.filter(
            transaction_type=DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_withdrawals = Transaction.objects.filter(
            transaction_type=WITHDRAWAL
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_interest = Transaction.objects.filter(
            transaction_type=INTEREST
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_transactions = Transaction.objects.filter(
            timestamp__gte=thirty_days_ago
        ).count()
        new_users = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        
        top_accounts = UserBankAccount.objects.select_related(
            'user', 'account_type'
        ).order_by('-balance')[:5]
        
        recent_txns = Transaction.objects.select_related(
            'account', 'account__user'
        ).order_by('-timestamp')[:10]
        
        context = {
            **self.each_context(request),
            'total_users': total_users,
            'total_accounts': total_accounts,
            'total_balance': total_balance,
            'total_transactions': total_transactions,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_interest': total_interest,
            'recent_transactions': recent_transactions,
            'new_users': new_users,
            'top_accounts': top_accounts,
            'recent_txns': recent_txns,
        }
        
        return render(request, 'admin/dashboard.html', context)


admin_site = BankingAdminSite(name='banking_admin')

admin_site.register(User, UserAdmin)
admin_site.register(BankAccountType, BankAccountTypeAdmin)
admin_site.register(UserBankAccount, UserBankAccountAdmin)
admin_site.register(UserAddress, UserAddressAdmin)

admin.site.register(BankAccountType, BankAccountTypeAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserAddress, UserAddressAdmin)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
admin.site.register(AuditLog)
