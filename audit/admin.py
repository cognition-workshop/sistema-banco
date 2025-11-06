from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'usuario', 'tipo_transacao', 'hash_atual']
    list_filter = ['tipo_transacao', 'timestamp']
    search_fields = ['usuario__email', 'hash_atual']
    readonly_fields = [
        'timestamp', 'usuario', 'tipo_transacao', 
        'dados_transacao', 'hash_anterior', 'hash_atual'
    ]
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request):
        return False
