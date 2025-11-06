from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'user', 'account', 'transaction_type', 'amount']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['user__email', 'current_hash']
    readonly_fields = [field.name for field in AuditLog._meta.fields]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
