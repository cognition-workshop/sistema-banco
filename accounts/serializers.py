from rest_framework import serializers
from .models import UserBankAccount


class UserBankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'balance']
        read_only_fields = ['account_no', 'balance']
