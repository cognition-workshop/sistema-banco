from rest_framework import serializers
from accounts.models import UserBankAccount


class AccountBalanceSerializer(serializers.ModelSerializer):
    account_no = serializers.IntegerField(read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'balance', 'account_type_name']
