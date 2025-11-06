from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.utils import timezone

from localization.models import ChavePIX, TransacaoPIX, Feriado, AuditLog
from localization.serializers import (
    UserSerializer, ChavePIXSerializer, TransacaoPIXSerializer,
    FeriadoSerializer, AuditLogSerializer, CadastrarChavePIXSerializer,
    TransferenciaPIXSerializer, GerarQRCodeSerializer,
    ProcessarQRCodeSerializer, CalcularPrazoSerializer
)
from localization.services.pix_service import PIXService
from localization.services.calendario_service import CalendarioService
from localization.services.audit_service import AuditService
from localization.services.report_service import ReportService

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de usuários com CPF"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def validar_cpf(self, request, pk=None):
        """Valida o CPF de um usuário"""
        user = self.get_object()
        if user.cpf:
            from localization.validators import validate_cpf
            try:
                validate_cpf(user.cpf)
                return Response({
                    'valido': True,
                    'cpf': user.cpf,
                    'mensagem': 'CPF válido'
                })
            except Exception as e:
                return Response({
                    'valido': False,
                    'cpf': user.cpf,
                    'mensagem': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'valido': False,
            'mensagem': 'CPF não cadastrado'
        }, status=status.HTTP_404_NOT_FOUND)


class ChavePIXViewSet(viewsets.ModelViewSet):
    """API para gerenciamento de chaves PIX"""
    serializer_class = ChavePIXSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChavePIX.objects.filter(usuario=self.request.user, ativa=True)
    
    def create(self, request):
        """Cadastrar nova chave PIX"""
        serializer = CadastrarChavePIXSerializer(data=request.data)
        if serializer.is_valid():
            try:
                chave = PIXService.cadastrar_chave(
                    usuario=request.user,
                    tipo=serializer.validated_data['tipo'],
                    chave=serializer.validated_data['chave']
                )
                return Response(
                    ChavePIXSerializer(chave).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'erro': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Remover (inativar) chave PIX"""
        try:
            chave = PIXService.remover_chave(pk, request.user)
            return Response(
                {'mensagem': 'Chave PIX removida com sucesso'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TransacaoPIXViewSet(viewsets.ModelViewSet):
    """API para transações PIX"""
    serializer_class = TransacaoPIXSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_account = self.request.user.account
        return TransacaoPIX.objects.filter(
            conta_origem=user_account
        ) | TransacaoPIX.objects.filter(
            conta_destino=user_account
        )
    
    def create(self, request):
        """Realizar transferência PIX"""
        serializer = TransferenciaPIXSerializer(data=request.data)
        if serializer.is_valid():
            try:
                conta_origem = request.user.account
                transacao = PIXService.realizar_transferencia(
                    conta_origem=conta_origem,
                    chave_destino=serializer.validated_data['chave_pix_destino'],
                    valor=serializer.validated_data['valor'],
                    descricao=serializer.validated_data.get('descricao', '')
                )
                
                AuditService.registrar_operacao(
                    usuario=request.user,
                    conta=conta_origem,
                    tipo_operacao='PIX',
                    valor=transacao.valor,
                    saldo_anterior=conta_origem.balance + transacao.valor,
                    saldo_posterior=conta_origem.balance,
                    descricao=f'PIX para {transacao.chave_pix_destino}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return Response(
                    TransacaoPIXSerializer(transacao).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'erro': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def gerar_qrcode(self, request):
        """Gerar QR Code PIX"""
        serializer = GerarQRCodeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                resultado = PIXService.gerar_qr_code(
                    chave_pix=serializer.validated_data['chave_pix'],
                    valor=serializer.validated_data.get('valor'),
                    descricao=serializer.validated_data.get('descricao', '')
                )
                return Response(resultado, status=status.HTTP_200_OK)
            except Exception as e:
                return Response(
                    {'erro': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def processar_qrcode(self, request):
        """Processar QR Code PIX para pagamento"""
        serializer = ProcessarQRCodeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                conta_origem = request.user.account
                transacao = PIXService.processar_qr_code(
                    payload=serializer.validated_data['payload'],
                    conta_origem=conta_origem
                )
                return Response(
                    TransacaoPIXSerializer(transacao).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'erro': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeriadoViewSet(viewsets.ReadOnlyModelViewSet):
    """API para consulta de feriados bancários"""
    queryset = Feriado.objects.all()
    serializer_class = FeriadoSerializer
    
    @action(detail=False, methods=['post'])
    def calcular_prazo(self, request):
        """Calcula prazo em dias úteis"""
        serializer = CalcularPrazoSerializer(data=request.data)
        if serializer.is_valid():
            data_inicio = serializer.validated_data['data_inicio']
            dias_uteis = serializer.validated_data['dias_uteis']
            
            data_fim = CalendarioService.calcular_prazo_dias_uteis(
                data_inicio, dias_uteis
            )
            
            return Response({
                'data_inicio': data_inicio,
                'dias_uteis': dias_uteis,
                'data_fim': data_fim
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API para consulta de logs de auditoria"""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AuditLog.objects.filter(usuario=self.request.user)
    
    @action(detail=True, methods=['get'])
    def verificar(self, request, pk=None):
        """Verifica integridade de um registro de auditoria"""
        resultado = AuditService.verificar_integridade(pk)
        return Response(resultado, status=status.HTTP_200_OK)


class RelatorioIRPFViewSet(viewsets.ViewSet):
    """API para geração de relatórios IRPF"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def gerar(self, request):
        """Gera relatório IRPF para um ano"""
        ano = int(request.query_params.get('ano', timezone.now().year))
        relatorio = ReportService.gerar_relatorio_irpf(request.user, ano)
        
        relatorio_data = {
            'ano': relatorio['ano'],
            'cpf': relatorio['cpf'],
            'total_depositos': str(relatorio['total_depositos']),
            'total_saques': str(relatorio['total_saques']),
            'total_juros': str(relatorio['total_juros']),
            'saldo_inicial': str(relatorio['saldo_inicial']),
            'saldo_final': str(relatorio['saldo_final']),
            'quantidade_transacoes': relatorio['quantidade_transacoes']
        }
        
        return Response(relatorio_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def pdf(self, request):
        """Download do relatório em PDF"""
        ano = int(request.query_params.get('ano', timezone.now().year))
        relatorio = ReportService.gerar_relatorio_irpf(request.user, ano)
        pdf_data = ReportService.exportar_pdf(relatorio)
        
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="irpf_{ano}.pdf"'
        return response
    
    @action(detail=False, methods=['get'])
    def csv(self, request):
        """Download do relatório em CSV"""
        ano = int(request.query_params.get('ano', timezone.now().year))
        relatorio = ReportService.gerar_relatorio_irpf(request.user, ano)
        csv_data = ReportService.exportar_csv(relatorio)
        
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="irpf_{ano}.csv"'
        return response
