from rest_framework import serializers
from .models import Transaction, ChavePix, TransacaoPix
from accounts.models import UserBankAccount


class ChavePixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChavePix
        fields = ['id', 'tipo_chave', 'chave', 'ativa', 'data_criacao']
        read_only_fields = ['id', 'data_criacao']


class TransacaoPixSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransacaoPix
        fields = ['transaction', 'chave_origem', 'chave_destino', 'qr_code_data']


class TransferirPixSerializer(serializers.Serializer):
    chave_destino = serializers.CharField(max_length=255)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)
    descricao = serializers.CharField(max_length=255, required=False)
