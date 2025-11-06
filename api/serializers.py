from rest_framework import serializers
from accounts.models import User, UserBankAccount, BankAccountType
from transactions.models import Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = '__all__'


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'balance', 
                 'gender', 'birth_date', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['id', 'account_no', 'balance', 'interest_start_date', 
                           'initial_deposit_date']


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', 
        read_only=True
    )
    
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'balance_after_transaction', 'transaction_type', 
                 'transaction_type_display', 'timestamp']
        read_only_fields = ['id', 'balance_after_transaction', 'timestamp']
