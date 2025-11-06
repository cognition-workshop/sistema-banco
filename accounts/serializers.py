from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserBankAccount, BankAccountType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = "__all__"


class BankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)

    class Meta:
        model = UserBankAccount
        fields = [
            "id",
            "user",
            "account_type",
            "account_no",
            "gender",
            "birth_date",
            "balance",
            "interest_start_date",
            "initial_deposit_date",
        ]
        read_only_fields = ["id", "account_no", "balance"]
