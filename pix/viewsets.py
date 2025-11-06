from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import ChavePix, TransacaoPix
from .serializers import (
    ChavePixSerializer, 
    TransacaoPixSerializer,
    PixTransferirSerializer,
    QRCodeSerializer
)
from .throttles import PixTransferThrottle
from transactions.models import Transaction
from transactions.constants import PIX_TRANSFER
import qrcode
import io
import base64


class ChavePixViewSet(viewsets.ModelViewSet):
    serializer_class = ChavePixSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChavePix.objects.filter(
            conta__user=self.request.user,
            ativa=True
        ).select_related('conta')
    
    def perform_create(self, serializer):
        serializer.save(conta=self.request.user.account)
    
    def perform_destroy(self, instance):
        instance.ativa = False
        instance.save()


class PixViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PixTransferThrottle]
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def transferir(self, request):
        serializer = PixTransferirSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chave_valor = serializer.validated_data['chave_destino']
        valor = serializer.validated_data['valor']
        descricao = serializer.validated_data.get('descricao', '')
        
        try:
            chave_destino = ChavePix.objects.select_related('conta').get(
                valor=chave_valor,
                ativa=True
            )
        except ChavePix.DoesNotExist:
            return Response(
                {'error': 'Chave PIX não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        conta_origem = request.user.account
        conta_destino = chave_destino.conta
        
        if conta_origem.balance < valor:
            return Response(
                {'error': 'Saldo insuficiente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if conta_origem == conta_destino:
            return Response(
                {'error': 'Não é possível transferir para a própria conta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transacao_pix = TransacaoPix.objects.create(
            conta_origem=conta_origem,
            conta_destino=conta_destino,
            chave_destino=chave_destino,
            valor=valor,
            descricao=descricao,
            status='PROCESSANDO'
        )
        
        try:
            conta_origem.balance -= valor
            conta_origem.save(update_fields=['balance'])
            
            conta_destino.balance += valor
            conta_destino.save(update_fields=['balance'])
            
            Transaction.objects.create(
                account=conta_origem,
                amount=valor,
                balance_after_transaction=conta_origem.balance,
                transaction_type=PIX_TRANSFER
            )
            
            Transaction.objects.create(
                account=conta_destino,
                amount=valor,
                balance_after_transaction=conta_destino.balance,
                transaction_type=PIX_TRANSFER
            )
            
            transacao_pix.status = 'CONCLUIDO'
            transacao_pix.save(update_fields=['status'])
            
            return Response(
                TransacaoPixSerializer(transacao_pix).data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            transacao_pix.status = 'FALHOU'
            transacao_pix.save(update_fields=['status'])
            raise
    
    @action(detail=False, methods=['post'])
    def qrcode(self, request):
        serializer = QRCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        chave_pix = serializer.validated_data['chave_pix']
        valor = serializer.validated_data['valor']
        descricao = serializer.validated_data.get('descricao', '')
        
        payload = f"PIX|{chave_pix}|{valor}|{descricao}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(payload)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'qr_code_image': f'data:image/png;base64,{img_str}',
            'payload': payload
        })
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def pagar_qrcode(self, request):
        payload = request.data.get('payload')
        
        if not payload:
            return Response(
                {'error': 'Payload do QR Code é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            parts = payload.split('|')
            chave_pix = parts[1]
            valor = float(parts[2])
            descricao = parts[3] if len(parts) > 3 else ''
        except (IndexError, ValueError):
            return Response(
                {'error': 'Payload inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transfer_data = {
            'chave_destino': chave_pix,
            'valor': valor,
            'descricao': descricao
        }
        
        request._full_data = transfer_data
        return self.transferir(request)
