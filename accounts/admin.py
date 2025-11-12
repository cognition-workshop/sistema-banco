from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import BankAccountType, User, UserAddress, UserBankAccount


class UserAddressInline(admin.StackedInline):
    model = UserAddress
    can_delete = False
    verbose_name_plural = 'Endereço'
    fields = ('street_address', 'city', 'postal_code', 'country')


class UserBankAccountInline(admin.StackedInline):
    model = UserBankAccount
    can_delete = False
    verbose_name_plural = 'Conta Bancária'
    readonly_fields = ('account_no', 'balance', 'initial_deposit_date', 'interest_start_date')
    fields = ('account_type', 'account_no', 'gender', 'birth_date', 'balance', 'initial_deposit_date', 'interest_start_date')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'account_number', 'balance_display', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    
    inlines = [UserBankAccountInline, UserAddressInline]
    
    actions = ['activate_users', 'deactivate_users']
    
    def account_number(self, obj):
        if hasattr(obj, 'account'):
            url = reverse('admin:accounts_userbankaccount_change', args=[obj.account.pk])
            return format_html('<a href="{}">{}</a>', url, obj.account.account_no)
        return '-'
    account_number.short_description = 'Número da Conta'
    
    def balance_display(self, obj):
        if hasattr(obj, 'account'):
            balance = obj.account.balance
            color = 'green' if balance > 0 else 'red'
            return format_html('<span style="color: {};">R$ {:.2f}</span>', color, balance)
        return '-'
    balance_display.short_description = 'Saldo'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuário(s) ativado(s) com sucesso.')
    activate_users.short_description = 'Ativar usuários selecionados'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuário(s) desativado(s) com sucesso.')
    deactivate_users.short_description = 'Desativar usuários selecionados'


@admin.register(BankAccountType)
class BankAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year', 'account_count')
    list_filter = ('interest_calculation_per_year',)
    search_fields = ('name',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name',)
        }),
        ('Configurações de Saque', {
            'fields': ('maximum_withdrawal_amount',)
        }),
        ('Configurações de Juros', {
            'fields': ('annual_interest_rate', 'interest_calculation_per_year')
        }),
    )
    
    def account_count(self, obj):
        count = obj.accounts.count()
        return count
    account_count.short_description = 'Número de Contas'


@admin.register(UserBankAccount)
class UserBankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_no', 'user_email', 'account_type', 'balance_display', 'gender', 'birth_date')
    list_filter = ('account_type', 'gender', 'initial_deposit_date')
    search_fields = ('account_no', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('account_no', 'balance', 'initial_deposit_date', 'interest_start_date')
    
    fieldsets = (
        ('Informações da Conta', {
            'fields': ('user', 'account_type', 'account_no')
        }),
        ('Informações Pessoais', {
            'fields': ('gender', 'birth_date')
        }),
        ('Informações Financeiras', {
            'fields': ('balance', 'initial_deposit_date', 'interest_start_date')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email do Usuário'
    
    def balance_display(self, obj):
        color = 'green' if obj.balance > 0 else 'red'
        return format_html('<span style="color: {};">R$ {:.2f}</span>', color, obj.balance)
    balance_display.short_description = 'Saldo'


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'postal_code')
    list_filter = ('country', 'city')
    search_fields = ('user__email', 'street_address', 'city', 'country')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
