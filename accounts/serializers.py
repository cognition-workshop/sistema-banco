from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserBankAccount, BankAccountType, UserAddress

User = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['street_address', 'city', 'postal_code', 'country']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                 'interest_calculation_per_year']
        read_only_fields = ['id']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    account_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccountType.objects.all(),
        source='account_type',
        write_only=True
    )
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'account_no', 'account_type', 'account_type_id', 'gender', 
                 'birth_date', 'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['id', 'account_no', 'balance', 'interest_start_date', 
                           'initial_deposit_date']


class UserSerializer(serializers.ModelSerializer):
    address = UserAddressSerializer(required=False)
    account = UserBankAccountSerializer(read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 
                 'date_joined', 'address', 'account', 'balance']
        read_only_fields = ['id', 'date_joined', 'balance']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        address_data = validated_data.pop('address', None)
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        if address_data:
            UserAddress.objects.create(user=user, **address_data)
        
        return user

    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        
        instance = super().update(instance, validated_data)
        
        if address_data:
            UserAddress.objects.update_or_create(
                user=instance,
                defaults=address_data
            )
        
        return instance
