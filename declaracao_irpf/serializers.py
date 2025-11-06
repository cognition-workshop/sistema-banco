from rest_framework import serializers
from .models import RelatorioIRPF


class RelatorioIRPFSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatorioIRPF
        fields = ['id', 'ano_calendario', 'rendimentos_juros', 'total_depositado',
                 'total_sacado', 'saldo_31_dezembro', 'gerado_em', 'arquivo_pdf']
        read_only_fields = ['id', 'gerado_em']
