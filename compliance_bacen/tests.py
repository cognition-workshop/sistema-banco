from django.test import TestCase
from compliance_bacen.models import BacenAuditLog


class AuditLogImmutabilityTests(TestCase):
    def test_cannot_delete_audit_log(self):
        """Test that audit logs cannot be deleted"""
        log = BacenAuditLog.objects.create(
            evento_tipo='USER_CREATED',
            dados_posteriores={'test': 'data'}
        )
        
        with self.assertRaises(NotImplementedError):
            log.delete()
    
    def test_cannot_update_audit_log(self):
        """Test that audit logs cannot be updated via manager"""
        log = BacenAuditLog.objects.create(
            evento_tipo='USER_CREATED',
            dados_posteriores={'test': 'data'}
        )
        
        with self.assertRaises(NotImplementedError):
            BacenAuditLog.objects.filter(id=log.id).update(evento_tipo='CHANGED')
    
    def test_hash_integrity(self):
        """Test hash chain integrity"""
        log1 = BacenAuditLog.objects.create(
            evento_tipo='USER_CREATED',
            dados_posteriores={'test': 'data1'}
        )
        
        log2 = BacenAuditLog.objects.create(
            evento_tipo='USER_UPDATED',
            dados_posteriores={'test': 'data2'},
            hash_anterior=log1.hash_integridade
        )
        
        self.assertEqual(log2.hash_anterior, log1.hash_integridade)
        self.assertIsNotNone(log2.hash_integridade)
        self.assertNotEqual(log1.hash_integridade, log2.hash_integridade)
