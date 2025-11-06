from rest_framework import serializers
from accounts.models import UserBankAccount


class AccountBalanceSerializer(serializers.ModelSerializer):
    accountId = serializers.CharField(source='account_no', read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    currency = serializers.SerializerMethodField()

    class Meta:
        model = UserBankAccount
        fields = ['accountId', 'balance', 'currency']

    def get_currency(self, obj):
        return 'BRL'
