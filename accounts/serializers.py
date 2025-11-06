from rest_framework import serializers
from .models import UserBankAccount


class AccountBalanceSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(
        source='account_type.name',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'balance', 'account_type_name', 'user_email']
        read_only_fields = ['account_no', 'balance', 'account_type_name', 'user_email']
