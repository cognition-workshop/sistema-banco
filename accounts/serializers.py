from rest_framework import serializers
from .models import User, UserBankAccount, BankAccountType, UserAddress


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = '__all__'


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    account_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccountType.objects.all(),
        source='account_type',
        write_only=True
    )
    
    class Meta:
        model = UserBankAccount
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'account', 'address', 'date_joined']
        read_only_fields = ['date_joined']
