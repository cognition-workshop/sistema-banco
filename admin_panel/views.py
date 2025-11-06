from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q

from .models import AdminUser, AuditLog, FraudRule, FraudAlert, SystemHealthMetric
from transactions.models import Transaction
from .serializers import (
    UserSerializer, TransactionSerializer, FraudRuleSerializer,
    FraudAlertSerializer, AuditLogSerializer, SystemHealthMetricSerializer,
    AnalyticsSerializer
)
from .permissions import IsAdminUser, IsSeniorAdmin, IsOperationalOrSeniorAdmin
from .analytics import Analytics
from .reports import ReportGenerator
from .health_monitor import HealthMonitor

User = get_user_model()


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        if not hasattr(self.user, 'admin_user'):
            raise serializers.ValidationError("User is not an admin")
        
        if not self.user.admin_user.is_admin_active:
            raise serializers.ValidationError("Admin account is not active")
        
        data['role'] = self.user.admin_user.role
        data['email'] = self.user.email
        
        return data


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
    permission_classes = [AllowAny]


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOperationalOrSeniorAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        name = self.request.query_params.get('name', None)
        email = self.request.query_params.get('email', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if name:
            queryset = queryset.filter(
                Q(first_name__icontains=name) | Q(last_name__icontains=name)
            )
        if email:
            queryset = queryset.filter(email__icontains=email)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.select_related('account', 'address')
    
    @action(detail=True, methods=['post'], permission_classes=[IsSeniorAdmin])
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        
        AuditLog.objects.create(
            admin_user=request.user.admin_user,
            action_type='SUSPEND',
            target_model='User',
            target_id=user.id,
            details={'email': user.email},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'status': 'user suspended'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsSeniorAdmin])
    def reactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        
        AuditLog.objects.create(
            admin_user=request.user.admin_user,
            action_type='REACTIVATE',
            target_model='User',
            target_id=user.id,
            details={'email': user.email},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'status': 'user reactivated'})


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        transaction_type = self.request.query_params.get('type', None)
        min_amount = self.request.query_params.get('min_amount', None)
        max_amount = self.request.query_params.get('max_amount', None)
        user_email = self.request.query_params.get('user_email', None)
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        if user_email:
            queryset = queryset.filter(account__user__email__icontains=user_email)
        
        return queryset.select_related('account', 'account__user').order_by('-timestamp')


class FraudRuleViewSet(viewsets.ModelViewSet):
    queryset = FraudRule.objects.all()
    serializer_class = FraudRuleSerializer
    permission_classes = [IsSeniorAdmin]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.admin_user)
        
        AuditLog.objects.create(
            admin_user=self.request.user.admin_user,
            action_type='CREATE',
            target_model='FraudRule',
            details={'name': serializer.instance.name},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )


class FraudAlertViewSet(viewsets.ModelViewSet):
    queryset = FraudAlert.objects.all()
    serializer_class = FraudAlertSerializer
    permission_classes = [IsOperationalOrSeniorAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('transaction', 'rule', 'reviewed_by').order_by('-detected_at')
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        alert = self.get_object()
        new_status = request.data.get('status', 'REVIEWED')
        notes = request.data.get('notes', '')
        
        alert.status = new_status
        alert.notes = notes
        alert.reviewed_by = request.user.admin_user
        alert.reviewed_at = timezone.now()
        alert.save()
        
        AuditLog.objects.create(
            admin_user=request.user.admin_user,
            action_type='UPDATE',
            target_model='FraudAlert',
            target_id=alert.id,
            details={'status': new_status, 'notes': notes},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(self.get_serializer(alert).data)


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def transaction_volume(self, request):
        analytics = Analytics()
        
        date_from = request.query_params.get('date_from', None)
        date_to = request.query_params.get('date_to', None)
        
        data = analytics.get_transaction_volume_by_type(date_from, date_to)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def daily_trends(self, request):
        analytics = Analytics()
        days = int(request.query_params.get('days', 30))
        
        data = analytics.get_daily_trends(days)
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def user_statistics(self, request):
        analytics = Analytics()
        data = analytics.get_user_statistics()
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def fraud_statistics(self, request):
        analytics = Analytics()
        data = analytics.get_fraud_statistics()
        return Response(data)


class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        format_type = request.query_params.get('format', 'csv')
        
        transactions = Transaction.objects.select_related('account', 'account__user').order_by('-timestamp')[:1000]
        
        generator = ReportGenerator()
        
        if format_type == 'pdf':
            pdf_data = generator.generate_transaction_pdf(transactions)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d")}.pdf"'
        else:
            csv_data = generator.generate_transaction_csv(transactions)
            response = HttpResponse(csv_data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def fraud_alerts(self, request):
        alerts = FraudAlert.objects.select_related('transaction', 'rule', 'reviewed_by').order_by('-detected_at')[:1000]
        
        generator = ReportGenerator()
        csv_data = generator.generate_fraud_alerts_csv(alerts)
        
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="fraud_alerts_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        return response


class SystemHealthViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        monitor = HealthMonitor()
        metrics = monitor.get_all_metrics()
        
        for metric_type, data in metrics.items():
            if metric_type in ['cpu', 'memory', 'database']:
                SystemHealthMetric.objects.create(
                    metric_type=metric_type.upper(),
                    value=data.get('usage_percent') or data.get('response_time_ms', 0),
                    details=data,
                    status=data['status']
                )
        
        return Response(metrics)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        hours = int(request.query_params.get('hours', 24))
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        
        metrics = SystemHealthMetric.objects.filter(
            timestamp__gte=time_threshold
        ).order_by('-timestamp')
        
        serializer = SystemHealthMetricSerializer(metrics, many=True)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSeniorAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        action_type = self.request.query_params.get('action_type', None)
        target_model = self.request.query_params.get('target_model', None)
        admin_email = self.request.query_params.get('admin_email', None)
        
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if target_model:
            queryset = queryset.filter(target_model=target_model)
        if admin_email:
            queryset = queryset.filter(admin_user__user__email__icontains=admin_email)
        
        return queryset.select_related('admin_user', 'admin_user__user')
