from rest_framework import serializers
from .models import User, UserBankAccount


class UserSerializer(serializers.ModelSerializer):
    cpf_formatted = serializers.CharField(source='cpf_formatted', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'cpf', 'cpf_formatted']


class UserBankAccountSerializer(serializers.ModelSerializer):
    formatted_account = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'agency', 
                  'account_number', 'account_digit', 'formatted_account', 
                  'balance', 'gender', 'birth_date']
