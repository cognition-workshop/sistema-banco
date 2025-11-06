import hashlib
from django.utils import timezone
from localization.models import AuditLog


class AuditService:
    """Serviço para log de auditoria imutável (BACEN)"""
    
    @staticmethod
    def _gerar_hash(registro):
        """Gera hash SHA-256 para um registro"""
        dados = f"{registro.usuario_id}:{registro.conta_id}:{registro.tipo_operacao}:"
        dados += f"{registro.valor}:{registro.saldo_anterior}:{registro.saldo_posterior}:"
        dados += f"{registro.descricao}:{registro.timestamp.isoformat()}:"
        dados += f"{registro.hash_anterior or ''}"
        
        return hashlib.sha256(dados.encode()).hexdigest()
    
    @staticmethod
    def registrar_operacao(usuario, conta, tipo_operacao, valor, saldo_anterior, 
                          saldo_posterior, descricao, ip_address=None):
        """Registra uma operação financeira no log de auditoria"""
        ultimo_registro = AuditLog.objects.filter(
            conta=conta
        ).order_by('-timestamp').first()
        
        hash_anterior = ultimo_registro.hash_registro if ultimo_registro else None
        
        registro = AuditLog(
            usuario=usuario,
            conta=conta,
            tipo_operacao=tipo_operacao,
            valor=valor,
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo_posterior,
            descricao=descricao,
            hash_anterior=hash_anterior,
            ip_address=ip_address
        )
        
        registro.save()
        
        registro.hash_registro = AuditService._gerar_hash(registro)
        registro.save(update_fields=['hash_registro'])
        
        return registro
    
    @staticmethod
    def verificar_integridade(registro_id):
        """Verifica a integridade de um registro e sua cadeia"""
        try:
            registro = AuditLog.objects.get(id=registro_id)
            
            hash_calculado = AuditService._gerar_hash(registro)
            if hash_calculado != registro.hash_registro:
                return {
                    'valido': False,
                    'mensagem': 'Hash do registro não corresponde.',
                    'registro_id': registro_id
                }
            
            if registro.hash_anterior:
                try:
                    registro_anterior = AuditLog.objects.get(
                        conta=registro.conta,
                        hash_registro=registro.hash_anterior
                    )
                    if registro_anterior.timestamp >= registro.timestamp:
                        return {
                            'valido': False,
                            'mensagem': 'Sequência temporal inválida.',
                            'registro_id': registro_id
                        }
                except AuditLog.DoesNotExist:
                    return {
                        'valido': False,
                        'mensagem': 'Registro anterior não encontrado na cadeia.',
                        'registro_id': registro_id
                    }
            
            return {
                'valido': True,
                'mensagem': 'Registro íntegro.',
                'registro_id': registro_id,
                'hash': registro.hash_registro
            }
        except AuditLog.DoesNotExist:
            return {
                'valido': False,
                'mensagem': 'Registro não encontrado.',
                'registro_id': registro_id
            }
