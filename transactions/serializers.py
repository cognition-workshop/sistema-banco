from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.IntegerField(source='account.account_no', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'account_number', 'amount', 'balance_after_transaction', 
                  'transaction_type', 'transaction_type_display', 'timestamp']
        read_only_fields = ['id', 'balance_after_transaction', 'timestamp']
