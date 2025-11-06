from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.files.base import ContentFile
from django.db.models import Sum
from .models import ChavePix, TransacaoPix, Transaction, RelatorioIRPF
from .serializers import ChavePixSerializer, TransferirPixSerializer
from .constants import PIX
from .utils.irpf import calcular_rendimentos_ano
from .utils.pdf_generator import gerar_pdf_irpf
import qrcode
import io
import base64


class ChavePixViewSet(viewsets.ModelViewSet):
    serializer_class = ChavePixSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChavePix.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PixViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def transferir(self, request):
        serializer = TransferirPixSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        chave_destino = serializer.validated_data['chave_destino']
        valor = serializer.validated_data['valor']
        
        try:
            chave_pix = ChavePix.objects.get(chave=chave_destino, ativa=True)
            conta_destino = chave_pix.user.account
        except ChavePix.DoesNotExist:
            return Response(
                {'error': 'Chave PIX não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        conta_origem = request.user.account
        
        if conta_origem.balance < valor:
            return Response(
                {'error': 'Saldo insuficiente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            conta_origem.balance -= valor
            conta_origem.save()
            
            trans_origem = Transaction.objects.create(
                account=conta_origem,
                amount=valor,
                balance_after_transaction=conta_origem.balance,
                transaction_type=PIX
            )
            
            conta_destino.balance += valor
            conta_destino.save()
            
            trans_destino = Transaction.objects.create(
                account=conta_destino,
                amount=valor,
                balance_after_transaction=conta_destino.balance,
                transaction_type=PIX
            )
            
            TransacaoPix.objects.create(
                transaction=trans_origem,
                chave_origem=conta_origem.user.chaves_pix.filter(ativa=True).first(),
                chave_destino=chave_destino
            )
            
            TransacaoPix.objects.create(
                transaction=trans_destino,
                chave_destino=chave_destino
            )
        
        return Response({
            'status': 'success',
            'transaction_id': trans_origem.id,
            'valor': str(valor)
        })
    
    @action(detail=False, methods=['post'])
    def gerar_qrcode(self, request):
        valor = request.data.get('valor')
        
        qr_data = f"PIX|{request.user.account.numero_conta}|{valor}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'qr_code_data': qr_data,
            'qr_code_image': f"data:image/png;base64,{img_str}"
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def anos_disponiveis_irpf(request):
    """List years with transactions for IRPF."""
    anos = Transaction.objects.filter(
        account__user=request.user
    ).dates('timestamp', 'year').values_list('timestamp__year', flat=True)
    
    return Response({'anos': list(set(anos))})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gerar_relatorio_irpf(request, ano):
    """Generate IRPF report for a specific year."""
    dados = calcular_rendimentos_ano(request.user, ano)
    
    relatorio, created = RelatorioIRPF.objects.get_or_create(
        user=request.user,
        ano_calendario=ano,
        defaults={
            'rendimentos_totais': dados['rendimentos_totais'],
            'rendimentos_isentos': dados['rendimentos_isentos'],
            'rendimentos_tributaveis': dados['rendimentos_tributaveis'],
        }
    )
    
    if not created:
        relatorio.rendimentos_totais = dados['rendimentos_totais']
        relatorio.rendimentos_isentos = dados['rendimentos_isentos']
        relatorio.rendimentos_tributaveis = dados['rendimentos_tributaveis']
        relatorio.save()
    
    pdf_buffer = gerar_pdf_irpf(relatorio)
    relatorio.arquivo_pdf.save(
        f'irpf_{request.user.id}_{ano}.pdf',
        ContentFile(pdf_buffer.read()),
        save=True
    )
    
    return Response({
        'id': relatorio.id,
        'ano': ano,
        'rendimentos_totais': str(relatorio.rendimentos_totais),
        'rendimentos_tributaveis': str(relatorio.rendimentos_tributaveis),
        'pdf_url': request.build_absolute_uri(relatorio.arquivo_pdf.url) if relatorio.arquivo_pdf else None
    })
