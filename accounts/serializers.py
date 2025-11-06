from rest_framework import serializers
from .models import User, BankAccountType, UserBankAccount, UserAddress


class BankAccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccountType
        fields = ['id', 'name', 'maximum_withdrawal_amount', 
                  'annual_interest_rate', 'interest_calculation_per_year']
    
    def validate_annual_interest_rate(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Interest rate must be between 0 and 100")
        return value
    
    def validate_interest_calculation_per_year(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Interest calculation must be between 1 and 12 times per year")
        return value


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['street_address', 'city', 'postal_code', 'country']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type = BankAccountTypeSerializer(read_only=True)
    account_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BankAccountType.objects.all(),
        source='account_type',
        write_only=True
    )
    
    class Meta:
        model = UserBankAccount
        fields = ['id', 'account_no', 'account_type', 'account_type_id', 'balance', 
                  'gender', 'birth_date', 'initial_deposit_date', 
                  'interest_start_date', 'user']
        read_only_fields = ['account_no', 'balance', 'initial_deposit_date', 
                           'interest_start_date']


class UserSerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 
                  'date_joined', 'password', 'account', 'address']
        read_only_fields = ['date_joined']
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
