from rest_framework import serializers
from .models import User, BankAccountType, UserBankAccount, UserAddress


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = '__all__'


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = '__all__'
        read_only_fields = ['account_no', 'balance', 'interest_start_date', 'initial_deposit_date']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'
        read_only_fields = ['user']
