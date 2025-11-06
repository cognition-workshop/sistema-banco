from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import BankAccountType, UserBankAccount, UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    balance = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined', 'balance']
        read_only_fields = ['id', 'date_joined', 'balance']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                  'interest_calculation_per_year']


class UserAddressSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserAddress
        fields = ['id', 'user', 'user_email', 'street_address', 'city', 
                  'postal_code', 'country']
        read_only_fields = ['id']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'user_email', 'account_type', 'account_type_name', 
                  'account_no', 'gender', 'gender_display', 'birth_date', 'balance', 
                  'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['id', 'account_no', 'balance']
