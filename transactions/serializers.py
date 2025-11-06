from rest_framework import serializers
from .models import Transaction
from accounts.serializers import BankAccountSerializer


class TransactionSerializer(serializers.ModelSerializer):
    account = BankAccountSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "amount",
            "balance_after_transaction",
            "transaction_type",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp", "balance_after_transaction"]
