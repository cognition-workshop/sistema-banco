from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserBankAccount, BankAccountType, UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'balance']
        read_only_fields = ['id', 'balance']


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 'annual_interest_rate', 
                 'interest_calculation_per_year']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'street_address', 'city', 'postal_code', 'country']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'user', 'account_type', 'account_no', 'gender', 
                 'birth_date', 'balance', 'interest_start_date', 'initial_deposit_date']
        read_only_fields = ['id', 'account_no', 'balance', 'interest_start_date', 
                           'initial_deposit_date']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    address = UserAddressSerializer()
    account_type = serializers.PrimaryKeyRelatedField(queryset=BankAccountType.objects.all())
    gender = serializers.ChoiceField(choices=['M', 'F'])
    birth_date = serializers.DateField()
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2', 
                 'address', 'account_type', 'gender', 'birth_date']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match")
        return data
    
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        account_type = validated_data.pop('account_type')
        gender = validated_data.pop('gender')
        birth_date = validated_data.pop('birth_date')
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        
        UserAddress.objects.create(user=user, **address_data)
        
        from django.conf import settings
        account_no = settings.ACCOUNT_NUMBER_START_FROM + user.id
        
        UserBankAccount.objects.create(
            user=user,
            account_type=account_type,
            account_no=account_no,
            gender=gender,
            birth_date=birth_date
        )
        
        return user
