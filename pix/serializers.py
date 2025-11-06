from rest_framework import serializers
from .models import ChavePix, TransacaoPix
from accounts.models import UserBankAccount


class ChavePixSerializer(serializers.ModelSerializer):
    conta_formatada = serializers.CharField(source='conta.conta_formatada', read_only=True)
    
    class Meta:
        model = ChavePix
        fields = ['id', 'tipo', 'valor', 'ativa', 'criada_em', 'conta_formatada']
        read_only_fields = ['id', 'criada_em', 'conta_formatada']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'account'):
            data['conta'] = request.user.account
        
        chave = ChavePix(**data)
        chave.clean()
        
        return data


class TransacaoPixSerializer(serializers.ModelSerializer):
    conta_origem_formatada = serializers.CharField(source='conta_origem.conta_formatada', read_only=True)
    conta_destino_formatada = serializers.CharField(source='conta_destino.conta_formatada', read_only=True)
    chave_valor = serializers.CharField(source='chave_destino.valor', read_only=True)
    
    class Meta:
        model = TransacaoPix
        fields = ['id', 'valor', 'descricao', 'status', 'timestamp', 
                 'conta_origem_formatada', 'conta_destino_formatada', 'chave_valor']
        read_only_fields = ['id', 'status', 'timestamp', 'conta_origem_formatada', 
                           'conta_destino_formatada', 'chave_valor']


class PixTransferirSerializer(serializers.Serializer):
    chave_destino = serializers.CharField(required=True)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    descricao = serializers.CharField(max_length=140, required=False, allow_blank=True)


class QRCodeSerializer(serializers.Serializer):
    chave_pix = serializers.CharField(required=True)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    descricao = serializers.CharField(max_length=140, required=False, allow_blank=True)
