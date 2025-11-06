from rest_framework import serializers
from .models import Transaction
from .constants import DEPOSIT, WITHDRAWAL
from django.conf import settings
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'account', 'amount', 'balance_after_transaction', 
                 'transaction_type', 'timestamp']
        read_only_fields = ['id', 'account', 'balance_after_transaction', 'timestamp']


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, 
                                      min_value=settings.MINIMUM_DEPOSIT_AMOUNT)
    
    def create(self, validated_data):
        account = self.context['request'].user.account
        amount = validated_data['amount']
        
        if not account.initial_deposit_date:
            now = timezone.now()
            next_interest_month = int(
                12 / account.account_type.interest_calculation_per_year
            )
            account.initial_deposit_date = now
            account.interest_start_date = (
                now + relativedelta(months=+next_interest_month)
            )
        
        account.balance += amount
        account.save(update_fields=['initial_deposit_date', 'balance', 'interest_start_date'])
        
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            balance_after_transaction=account.balance,
            transaction_type=DEPOSIT
        )
        
        return transaction


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2,
                                      min_value=settings.MINIMUM_WITHDRAWAL_AMOUNT)
    
    def validate_amount(self, value):
        account = self.context['request'].user.account
        
        if value > account.account_type.maximum_withdrawal_amount:
            raise serializers.ValidationError(
                f"Amount exceeds maximum withdrawal limit of {account.account_type.maximum_withdrawal_amount}"
            )
        
        if value > account.balance:
            raise serializers.ValidationError("Insufficient balance")
        
        return value
    
    def create(self, validated_data):
        account = self.context['request'].user.account
        amount = validated_data['amount']
        
        account.balance -= amount
        account.save(update_fields=['balance'])
        
        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            balance_after_transaction=account.balance,
            transaction_type=WITHDRAWAL
        )
        
        return transaction
