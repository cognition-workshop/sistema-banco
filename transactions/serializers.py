from rest_framework import serializers
from .models import Transaction
from accounts.serializers import UserBankAccountSerializer


class TransactionSerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'amount', 'balance_after_transaction',
            'transaction_type', 'timestamp'
        ]
        read_only_fields = ['id', 'balance_after_transaction', 'timestamp']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('O valor deve ser maior que zero')
        return value
