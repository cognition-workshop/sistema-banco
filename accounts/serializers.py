from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BankAccountType, UserBankAccount, UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined', 'balance']
        read_only_fields = ['date_joined', 'balance']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                  'interest_calculation_per_year']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'street_address', 'city', 'postal_code', 'country']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'gender', 'birth_date',
                  'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['account_no', 'balance', 'interest_start_date', 'initial_deposit_date']
