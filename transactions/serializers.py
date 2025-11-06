from rest_framework import serializers
from django.conf import settings
from .models import Transaction
from .constants import DEPOSIT, WITHDRAWAL


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'amount', 'balance_after_transaction',
                  'transaction_type', 'transaction_type_display', 'timestamp']
        read_only_fields = ['balance_after_transaction', 'timestamp']
    
    def validate_amount(self, value):
        transaction_type = self.initial_data.get('transaction_type')
        
        if transaction_type == DEPOSIT:
            if value < settings.MINIMUM_DEPOSIT_AMOUNT:
                raise serializers.ValidationError(
                    f'Minimum deposit amount is {settings.MINIMUM_DEPOSIT_AMOUNT}'
                )
        elif transaction_type == WITHDRAWAL:
            if value < settings.MINIMUM_WITHDRAWAL_AMOUNT:
                raise serializers.ValidationError(
                    f'Minimum withdrawal amount is {settings.MINIMUM_WITHDRAWAL_AMOUNT}'
                )
        
        return value
    
    def validate(self, data):
        account = data.get('account')
        amount = data.get('amount')
        transaction_type = data.get('transaction_type')
        
        if transaction_type == WITHDRAWAL:
            if account.balance < amount:
                raise serializers.ValidationError(
                    "Insufficient funds for withdrawal"
                )
            
            max_withdrawal = account.account_type.maximum_withdrawal_amount
            if amount > max_withdrawal:
                raise serializers.ValidationError(
                    f'Maximum withdrawal amount is {max_withdrawal}'
                )
        
        return data
    
    def create(self, validated_data):
        account = validated_data['account']
        amount = validated_data['amount']
        transaction_type = validated_data['transaction_type']
        
        if transaction_type == DEPOSIT:
            account.balance += amount
        elif transaction_type == WITHDRAWAL:
            account.balance -= amount
        
        validated_data['balance_after_transaction'] = account.balance
        transaction = Transaction.objects.create(**validated_data)
        account.save()
        
        return transaction
