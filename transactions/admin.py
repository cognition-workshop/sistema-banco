from django.contrib import admin
from django.utils.html import format_html

<<<<<<< HEAD
from .models import Transaction, FraudAlert
||||||| 3b88f86
from transactions.models import Transaction
=======
from transactions.models import Transaction, ChavePix, TransferenciaPix
>>>>>>> 95130f10c6c0e6762b41f261beb96f020e992ef9

<<<<<<< HEAD

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'transaction_type_display', 'amount', 'balance_after_transaction', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['account__account_no', 'account__user__email']
    readonly_fields = ['account', 'amount', 'balance_after_transaction', 'transaction_type', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def account_no(self, obj):
        return obj.account.account_no
    account_no.short_description = 'Account Number'
    
    def transaction_type_display(self, obj):
        colors = {1: 'green', 2: 'red', 3: 'blue'}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.transaction_type, 'black'),
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Type'


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ['account_no', 'alert_type', 'severity', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['account__account_no', 'account__user__email', 'description']
    readonly_fields = ['account', 'alert_type', 'severity', 'description', 'transaction', 'created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_unresolved']
    
    def account_no(self, obj):
        return obj.account.account_no
    account_no.short_description = 'Account Number'
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} alert(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_at=None)
        self.message_user(request, f'{updated} alert(s) marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected alerts as unresolved'
||||||| 3b88f86
admin.site.register(Transaction)
=======

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'transaction_type', 'amount', 'timestamp', 'transaction_hash']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['transaction_hash', 'account__cpf']
    readonly_fields = ['transaction_hash', 'timestamp']
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChavePix)
class ChavePixAdmin(admin.ModelAdmin):
    list_display = ['chave', 'tipo', 'account', 'ativa']
    list_filter = ['tipo', 'ativa']
    search_fields = ['chave']


@admin.register(TransferenciaPix)
class TransferenciaPixAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'chave_destino_valor', 'status']
    list_filter = ['status']
>>>>>>> 95130f10c6c0e6762b41f261beb96f020e992ef9
