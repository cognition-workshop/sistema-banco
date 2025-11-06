from rest_framework import serializers
from .models import User, UserBankAccount, BankAccountType, UserAddress


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 'interest_calculation_per_year']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'gender', 'birth_date', 'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['account_no', 'balance']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'street_address', 'city', 'postal_code', 'country']
