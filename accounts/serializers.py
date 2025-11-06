from rest_framework import serializers
from .models import User, BankAccountType, UserBankAccount, UserAddress


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'balance']
        read_only_fields = ['id', 'date_joined', 'balance']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year']
        read_only_fields = ['id']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = [
            'id', 'user', 'account_type', 'account_no', 'gender', 
            'birth_date', 'balance', 'interest_start_date', 'initial_deposit_date'
        ]
        read_only_fields = ['id', 'account_no', 'balance']


class UserAddressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserAddress
        fields = ['id', 'user', 'street_address', 'city', 'postal_code', 'country']
        read_only_fields = ['id']
