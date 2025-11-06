from rest_framework import serializers
from .models import Transaction
from .constants import TRANSACTION_TYPE_CHOICES


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    account_no = serializers.IntegerField(
        source='account.account_no',
        read_only=True
    )
    
    def is_valid(self, raise_exception=False):
        if self.initial_data:
            self._errors = {'non_field_errors': ['This serializer is read-only and does not accept data for creation or updates.']}
            if raise_exception:
                raise serializers.ValidationError(self.errors)
            return False
        return super().is_valid(raise_exception=raise_exception)
    
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'account_no', 'amount', 'balance_after_transaction',
                 'transaction_type', 'transaction_type_display', 'timestamp']
        read_only_fields = ['id', 'account', 'account_no', 'amount', 
                           'balance_after_transaction', 'transaction_type', 
                           'transaction_type_display', 'timestamp']
