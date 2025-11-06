from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from .models import RelatorioIRPF
from .serializers import RelatorioIRPFSerializer


class RelatorioIRPFViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RelatorioIRPFSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RelatorioIRPF.objects.filter(usuario=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='(?P<ano>[0-9]{4})')
    def por_ano(self, request, ano=None):
        """Get IRPF report for specific year"""
        try:
            relatorio = RelatorioIRPF.objects.get(
                usuario=request.user,
                ano_calendario=ano
            )
            serializer = self.get_serializer(relatorio)
            return Response(serializer.data)
        except RelatorioIRPF.DoesNotExist:
            return Response(
                {'error': 'Relatório não encontrado para este ano'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download PDF report"""
        relatorio = self.get_object()
        if not relatorio.arquivo_pdf:
            return Response(
                {'error': 'PDF não disponível'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            relatorio.arquivo_pdf.open('rb'),
            as_attachment=True,
            filename=f'irpf_{relatorio.ano_calendario}.pdf'
        )
