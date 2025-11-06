from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount
from localization.models import ChavePIX, TransacaoPIX, Feriado, AuditLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'cpf']
        extra_kwargs = {
            'cpf': {'required': False}
        }


class UserBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankAccount
        fields = ['id', 'account_no', 'agencia', 'conta', 'balance']


class ChavePIXSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChavePIX
        fields = ['id', 'tipo', 'chave', 'ativa', 'data_cadastro']
        read_only_fields = ['id', 'ativa', 'data_cadastro']


class TransacaoPIXSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransacaoPIX
        fields = [
            'id', 'conta_origem', 'conta_destino', 'chave_pix_destino',
            'valor', 'descricao', 'status', 'data_transacao',
            'identificador_transacao', 'qr_code'
        ]
        read_only_fields = [
            'id', 'conta_destino', 'status', 'data_transacao',
            'identificador_transacao', 'qr_code'
        ]


class FeriadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feriado
        fields = ['id', 'nome', 'data', 'tipo', 'recorrente']


class AuditLogSerializer(serializers.ModelSerializer):
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'usuario', 'usuario_email', 'conta', 'tipo_operacao',
            'valor', 'saldo_anterior', 'saldo_posterior', 'descricao',
            'timestamp', 'hash_registro', 'hash_anterior', 'ip_address'
        ]
        read_only_fields = '__all__'


class CadastrarChavePIXSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['CPF', 'EMAIL', 'TELEFONE', 'ALEATORIA'])
    chave = serializers.CharField(max_length=255)


class TransferenciaPIXSerializer(serializers.Serializer):
    chave_pix_destino = serializers.CharField(max_length=255)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)
    descricao = serializers.CharField(max_length=255, required=False, allow_blank=True)


class GerarQRCodeSerializer(serializers.Serializer):
    chave_pix = serializers.CharField(max_length=255)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    descricao = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ProcessarQRCodeSerializer(serializers.Serializer):
    payload = serializers.CharField()


class CalcularPrazoSerializer(serializers.Serializer):
    data_inicio = serializers.DateField()
    dias_uteis = serializers.IntegerField(min_value=1)
