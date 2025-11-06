import uuid
import qrcode
from io import BytesIO
from decimal import Decimal
from django.db import transaction, models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from localization.models import ChavePIX, TransacaoPIX
from accounts.models import UserBankAccount


class PIXService:
    """Serviço para operações PIX"""
    
    @staticmethod
    def cadastrar_chave(usuario, tipo, chave):
        """Cadastra uma nova chave PIX"""
        if ChavePIX.objects.filter(chave=chave, ativa=True).exists():
            raise ValidationError('Esta chave PIX já está cadastrada.')
        
        if usuario.chaves_pix.filter(ativa=True).count() >= 5:
            raise ValidationError('Limite de 5 chaves PIX atingido.')
        
        chave_pix = ChavePIX.objects.create(
            usuario=usuario,
            tipo=tipo,
            chave=chave
        )
        return chave_pix
    
    @staticmethod
    def remover_chave(chave_id, usuario):
        """Remove (inativa) uma chave PIX"""
        try:
            chave = ChavePIX.objects.get(id=chave_id, usuario=usuario, ativa=True)
            chave.ativa = False
            chave.data_inativacao = timezone.now()
            chave.save()
            return chave
        except ChavePIX.DoesNotExist:
            raise ValidationError('Chave PIX não encontrada.')
    
    @staticmethod
    def listar_chaves(usuario):
        """Lista todas as chaves PIX ativas do usuário"""
        return ChavePIX.objects.filter(usuario=usuario, ativa=True)
    
    @staticmethod
    @transaction.atomic
    def realizar_transferencia(conta_origem, chave_destino, valor, descricao=''):
        """Realiza uma transferência PIX"""
        if valor <= 0:
            raise ValidationError('Valor deve ser maior que zero.')
        
        limite_transacao = getattr(settings, 'PIX_TRANSACTION_LIMIT', Decimal('1000.00'))
        if valor > limite_transacao:
            raise ValidationError(f'Valor excede o limite por transação de R$ {limite_transacao}.')
        
        limite_diario = getattr(settings, 'PIX_DAILY_LIMIT', Decimal('5000.00'))
        hoje = timezone.now().date()
        total_hoje = TransacaoPIX.objects.filter(
            conta_origem=conta_origem,
            data_transacao__date=hoje,
            status='CONCLUIDA'
        ).aggregate(total=models.Sum('valor'))['total'] or Decimal('0.00')
        
        if total_hoje + valor > limite_diario:
            raise ValidationError(f'Limite diário de R$ {limite_diario} excedido.')
        
        if conta_origem.balance < valor:
            raise ValidationError('Saldo insuficiente.')
        
        try:
            chave_pix = ChavePIX.objects.get(chave=chave_destino, ativa=True)
            conta_destino = chave_pix.usuario.account
        except ChavePIX.DoesNotExist:
            raise ValidationError('Chave PIX não encontrada.')
        except Exception:
            raise ValidationError('Erro ao buscar conta destino.')
        
        if conta_origem.id == conta_destino.id:
            raise ValidationError('Não é possível transferir para a própria conta.')
        
        identificador = str(uuid.uuid4())
        transacao = TransacaoPIX.objects.create(
            conta_origem=conta_origem,
            conta_destino=conta_destino,
            chave_pix_destino=chave_destino,
            valor=valor,
            descricao=descricao,
            identificador_transacao=identificador,
            status='PENDENTE'
        )
        
        try:
            conta_origem.balance -= valor
            conta_origem.save(update_fields=['balance'])
            
            conta_destino.balance += valor
            conta_destino.save(update_fields=['balance'])
            
            transacao.status = 'CONCLUIDA'
            transacao.save(update_fields=['status'])
            
            return transacao
        except Exception as e:
            transacao.status = 'FALHA'
            transacao.save(update_fields=['status'])
            raise ValidationError(f'Erro ao realizar transferência: {str(e)}')
    
    @staticmethod
    def gerar_qr_code(chave_pix, valor=None, descricao=''):
        """Gera QR Code PIX"""
        payload = f'PIX:{chave_pix}'
        if valor:
            payload += f':VALOR:{valor}'
        if descricao:
            payload += f':DESC:{descricao}'
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(payload)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        import base64
        qr_code_base64 = base64.b64encode(buffer.read()).decode()
        
        return {
            'qr_code': qr_code_base64,
            'payload': payload
        }
    
    @staticmethod
    def processar_qr_code(payload, conta_origem):
        """Processa um QR Code PIX para realizar pagamento"""
        try:
            partes = payload.split(':')
            if partes[0] != 'PIX':
                raise ValidationError('QR Code inválido.')
            
            chave_destino = partes[1]
            valor = None
            descricao = ''
            
            for i in range(2, len(partes), 2):
                if i + 1 < len(partes):
                    if partes[i] == 'VALOR':
                        valor = Decimal(partes[i + 1])
                    elif partes[i] == 'DESC':
                        descricao = partes[i + 1]
            
            if not valor:
                raise ValidationError('Valor não especificado no QR Code.')
            
            return PIXService.realizar_transferencia(
                conta_origem=conta_origem,
                chave_destino=chave_destino,
                valor=valor,
                descricao=descricao
            )
        except Exception as e:
            raise ValidationError(f'Erro ao processar QR Code: {str(e)}')
