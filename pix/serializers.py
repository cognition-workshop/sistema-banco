from rest_framework import serializers
from .models import PixKey, PixKeyType
from accounts.serializers import UserBankAccountSerializer


class PixKeySerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    account_id = serializers.PrimaryKeyRelatedField(
        source='account',
        read_only=True
    )

    class Meta:
        model = PixKey
        fields = ['id', 'account', 'account_id', 'key_type', 'key_value', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at']


class PixTransferSerializer(serializers.Serializer):
    pix_key = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)

    def validate_pix_key(self, value):
        try:
            pix_key = PixKey.objects.get(key_value=value, is_active=True)
            self.context['pix_key_obj'] = pix_key
            return value
        except PixKey.DoesNotExist:
            raise serializers.ValidationError('PIX key not found')

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'account'):
            sender_account = request.user.account
            amount = data.get('amount')

            if amount > sender_account.balance:
                raise serializers.ValidationError(
                    {'amount': f'Insufficient balance. Current balance: {sender_account.balance}'}
                )

            pix_key = self.context.get('pix_key_obj')
            if pix_key and pix_key.account == sender_account:
                raise serializers.ValidationError(
                    {'pix_key': 'Cannot transfer to your own account'}
                )

        return data
