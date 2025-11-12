from rest_framework import serializers
from django.conf import settings
from django.db import transaction
from .models import User, UserBankAccount, BankAccountType, UserAddress


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserAddressSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserAddress
        fields = ['id', 'street_address', 'city', 'postal_code', 'country']
        read_only_fields = ['id']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount']
        read_only_fields = ['id']


class UserBankAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account_type = BankAccountTypeSerializer(read_only=True)
    account_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccountType.objects.all(),
        source='account_type',
        write_only=True
    )
    
    class Meta:
        model = UserBankAccount
        fields = [
            'id', 'user', 'account_no', 'account_type', 'account_type_id',
            'gender', 'birth_date', 'balance', 'initial_deposit_date'
        ]
        read_only_fields = ['id', 'user', 'account_no', 'balance', 'initial_deposit_date']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    account_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccountType.objects.all(),
        write_only=True
    )
    gender = serializers.ChoiceField(choices=['M', 'F'])
    birth_date = serializers.DateField()
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 
                  'account_type_id', 'gender', 'birth_date']
    
    @transaction.atomic
    def create(self, validated_data):
        account_type = validated_data.pop('account_type_id')
        gender = validated_data.pop('gender')
        birth_date = validated_data.pop('birth_date')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        UserBankAccount.objects.create(
            user=user,
            gender=gender,
            birth_date=birth_date,
            account_type=account_type,
            account_no=(
                user.id +
                settings.ACCOUNT_NUMBER_START_FROM
            )
        )
        
        return user
