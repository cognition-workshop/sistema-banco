from rest_framework import serializers
from .models import UserBankAccount


class BankAccountTypeSerializer(serializers.Serializer):
    name = serializers.CharField()


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'balance', 'account_type']
        read_only_fields = ['account_no', 'balance', 'account_type']
