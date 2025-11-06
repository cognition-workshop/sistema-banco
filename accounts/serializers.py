from rest_framework import serializers
from decimal import Decimal


class BalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    account_no = serializers.IntegerField(allow_null=True)
    
    def to_representation(self, instance):
        account = getattr(instance, 'account', None)
        return {
            'balance': account.balance if account else Decimal('0.00'),
            'account_no': account.account_no if account else None,
        }
