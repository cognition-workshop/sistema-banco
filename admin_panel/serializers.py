from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import UserBankAccount, UserAddress
from transactions.models import Transaction
from .models import AdminUser, AuditLog, FraudRule, FraudAlert, SystemHealthMetric

User = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['street_address', 'city', 'postal_code', 'country']


class UserBankAccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(source='account_type.name', read_only=True)
    
    class Meta:
        model = UserBankAccount
        fields = ['account_no', 'account_type_name', 'gender', 'birth_date', 'balance', 'initial_deposit_date']
        read_only_fields = ['account_no', 'balance']


class UserSerializer(serializers.ModelSerializer):
    account = UserBankAccountSerializer(read_only=True)
    address = UserAddressSerializer(read_only=True)
    is_active = serializers.BooleanField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 
                  'is_staff', 'date_joined', 'account', 'address']
        read_only_fields = ['id', 'date_joined']


class TransactionSerializer(serializers.ModelSerializer):
    account_no = serializers.CharField(source='account.account_no', read_only=True)
    user_email = serializers.CharField(source='account.user.email', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'account_no', 'user_email', 'amount', 'balance_after_transaction',
                  'transaction_type', 'transaction_type_display', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class FraudRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    created_by_email = serializers.CharField(source='created_by.user.email', read_only=True)
    
    class Meta:
        model = FraudRule
        fields = ['id', 'name', 'rule_type', 'rule_type_display', 'parameters', 
                  'is_active', 'severity', 'created_at', 'updated_at', 
                  'created_by_email']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_email']


class FraudAlertSerializer(serializers.ModelSerializer):
    transaction = TransactionSerializer(read_only=True)
    rule = FraudRuleSerializer(read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FraudAlert
        fields = ['id', 'transaction', 'rule', 'detected_at', 'status', 
                  'status_display', 'reviewed_by_email', 'reviewed_at', 'notes']
        read_only_fields = ['id', 'transaction', 'rule', 'detected_at']


class AuditLogSerializer(serializers.ModelSerializer):
    admin_email = serializers.CharField(source='admin_user.user.email', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'admin_email', 'action_type', 'action_type_display', 
                  'target_model', 'target_id', 'details', 'timestamp', 'ip_address']
        read_only_fields = ['id', 'timestamp']


class SystemHealthMetricSerializer(serializers.ModelSerializer):
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    
    class Meta:
        model = SystemHealthMetric
        fields = ['id', 'metric_type', 'metric_type_display', 'value', 
                  'details', 'timestamp', 'status']
        read_only_fields = ['id', 'timestamp']


class AnalyticsSerializer(serializers.Serializer):
    transaction_volume_by_type = serializers.ListField(child=serializers.DictField())
    daily_trends = serializers.ListField(child=serializers.DictField())
    user_statistics = serializers.DictField()
