from django.http import HttpResponse
import csv
from datetime import datetime
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import BacenAuditLog


class IsAdminStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class BacenAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BacenAuditLog.objects.all()
    permission_classes = [IsAdminStaffPermission]
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export audit logs to CSV for BACEN"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="audit_log_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Timestamp', 'Evento', 'Usuario', 'Conta', 'Hash', 'Hash Anterior'])
        
        for log in BacenAuditLog.objects.all():
            writer.writerow([
                str(log.id),
                log.timestamp,
                log.evento_tipo,
                log.usuario.email if log.usuario else '',
                log.conta_afetada.conta_formatada if log.conta_afetada else '',
                log.hash_integridade,
                log.hash_anterior or ''
            ])
        
        return response
