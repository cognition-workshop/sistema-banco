from rest_framework import serializers
from .models import UserBankAccount, BankAccountType


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['name', 'maximum_withdrawal_amount', 'annual_interest_rate']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = [
            'account_no',
            'balance',
            'account_type',
            'initial_deposit_date',
            'interest_start_date',
        ]
        read_only_fields = fields
