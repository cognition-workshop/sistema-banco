from django.contrib import admin
from .models import BacenAuditLog


@admin.register(BacenAuditLog)
class BacenAuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'evento_tipo', 'usuario', 'conta_afetada']
    list_filter = ['evento_tipo', 'timestamp']
    search_fields = ['usuario__email', 'conta_afetada__account_no']
    readonly_fields = ['id', 'timestamp', 'hash_integridade', 'hash_anterior']
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
