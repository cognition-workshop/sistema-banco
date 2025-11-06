from rest_framework import serializers
from accounts.models import User, UserBankAccount
from transactions.models import Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class AccountSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'account_no', 'balance', 'account_type', 'account_type_name', 
                  'user', 'user_email', 'gender', 'birth_date']
        read_only_fields = ['balance']


class TransactionSerializer(serializers.ModelSerializer):
    account_no = serializers.IntegerField(source='account.account_no', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'account_no', 'transaction_type', 'amount', 
                  'balance_after_transaction', 'timestamp']
        read_only_fields = ['balance_after_transaction', 'timestamp']
