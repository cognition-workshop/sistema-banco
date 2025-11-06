from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserBankAccount, UserAddress, BankAccountType

User = get_user_model()


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                  'interest_calculation_per_year']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['street_address', 'city', 'postal_code', 'country']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'account_type', 'gender', 'birth_date', 
                  'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['account_no', 'balance']


class UserSerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'account', 'address']
        read_only_fields = ['id']
