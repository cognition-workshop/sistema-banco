from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import BankAccountType, UserBankAccount, UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    balance = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'balance', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'balance']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                  'interest_calculation_per_year']
        read_only_fields = ['id']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'street_address', 'city', 'postal_code', 'country']
        read_only_fields = ['id']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'gender', 'birth_date', 
                  'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['id', 'account_no', 'balance', 'interest_start_date', 
                           'initial_deposit_date']


class UserBankAccountDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    address = UserAddressSerializer(source='user.address', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'gender', 'birth_date', 
                  'balance', 'interest_start_date', 'initial_deposit_date', 'address']
        read_only_fields = ['id', 'account_no', 'balance', 'interest_start_date', 
                           'initial_deposit_date']
