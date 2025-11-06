from rest_framework import serializers
from accounts.models import UserBankAccount


class AccountBalanceSerializer(serializers.ModelSerializer):
    account_type = serializers.SlugRelatedField(slug_field='name', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'balance', 'account_type', 'initial_deposit_date']
        read_only_fields = ['account_no', 'balance']
