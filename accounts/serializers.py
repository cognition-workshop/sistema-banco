from rest_framework import serializers
from .models import User, UserBankAccount, UserAddress, BankAccountType


from decimal import Decimal

class UserSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True,
        max_value=Decimal('9999999999.99'),
        min_value=Decimal('0.00')
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'balance', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'balance']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'


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
        read_only_fields = ['account_no', 'balance']
