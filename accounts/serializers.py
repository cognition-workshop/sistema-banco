from rest_framework import serializers
from .models import UserBankAccount


class UserBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankAccount
        fields = ['balance', 'account_no']
        read_only_fields = ['balance', 'account_no']
