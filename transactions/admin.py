from django.contrib import admin
from django.utils.html import format_html
from transactions.models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'account', 'transaction_type', 'amount', 
        'user', 'timestamp', 'hash_status'
    ]
    list_filter = ['transaction_type', 'is_deleted', 'timestamp']
    search_fields = ['account__account_no', 'user__email', 'ip_address']
    readonly_fields = [
        'account', 'amount', 'previous_balance', 'balance_after_transaction',
        'transaction_type', 'timestamp', 'user', 'ip_address',
        'previous_hash', 'current_hash', 'metadata', 'hash_verification_status'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def hash_status(self, obj):
        """Display hash verification status with color coding."""
        is_valid = obj.verify_hash_integrity()
        color = 'green' if is_valid else 'red'
        status = '✓ Valid' if is_valid else '✗ Invalid'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, status
        )
    hash_status.short_description = 'Hash Integrity'
    
    def hash_verification_status(self, obj):
        """Show detailed hash verification information."""
        hash_valid = obj.verify_hash_integrity()
        chain_valid = obj.verify_chain_integrity()
        
        return format_html(
            '<strong>Hash Valid:</strong> {}<br>'
            '<strong>Chain Valid:</strong> {}<br>'
            '<strong>Current Hash:</strong> {}<br>'
            '<strong>Previous Hash:</strong> {}',
            '✓ Yes' if hash_valid else '✗ No',
            '✓ Yes' if chain_valid else '✗ No',
            obj.current_hash,
            obj.previous_hash or 'N/A (First transaction)'
        )
    hash_verification_status.short_description = 'Verification Details'
