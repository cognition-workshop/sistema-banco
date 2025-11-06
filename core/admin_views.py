from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import timedelta
import redis
import psutil
from celery import current_app
from core.mixins import AdminRequiredMixin
from core.models import FraudAlert
from core.analytics import AnalyticsService
from transactions.models import Transaction
from accounts.models import UserBankAccount, User
from django.conf import settings


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        context.update({
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_accounts': UserBankAccount.objects.count(),
            'total_balance': UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0,
            'total_transactions': Transaction.objects.count(),
            'recent_transactions': Transaction.objects.count() - Transaction.objects.filter(
                timestamp__lt=thirty_days_ago
            ).count(),
            'pending_alerts': FraudAlert.objects.filter(status='PENDING').count(),
            'top_accounts': AnalyticsService.get_top_accounts_by_balance(limit=5),
        })
        
        return context


class AnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        days = int(self.request.GET.get('days', 30))
        volume_data = AnalyticsService.get_transaction_volume_by_period(days=days)
        
        type_distribution = AnalyticsService.get_transaction_type_distribution()
        
        context.update({
            'volume_data': list(volume_data),
            'type_distribution': list(type_distribution),
            'days': days,
        })
        
        return context


class AnalyticsDataAPIView(AdminRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        chart_type = request.GET.get('type', 'volume')
        days = int(request.GET.get('days', 30))
        
        if chart_type == 'volume':
            data = AnalyticsService.get_transaction_volume_by_period(days=days)
            return JsonResponse({
                'labels': [str(item['date']) for item in data],
                'datasets': [{
                    'label': 'Transaction Volume',
                    'data': [float(item['total_amount']) for item in data],
                }]
            })
        
        elif chart_type == 'balance':
            data = AnalyticsService.get_balance_growth_data(days=days)
            daily_balances = {}
            for item in data:
                date_str = str(item['date'])
                if date_str not in daily_balances:
                    daily_balances[date_str] = []
                daily_balances[date_str].append(float(item['balance']))
            
            return JsonResponse({
                'labels': list(daily_balances.keys()),
                'datasets': [{
                    'label': 'Total System Balance',
                    'data': [sum(balances) for balances in daily_balances.values()],
                }]
            })
        
        elif chart_type == 'distribution':
            data = AnalyticsService.get_transaction_type_distribution()
            type_names = {1: 'Deposits', 2: 'Withdrawals', 3: 'Interest'}
            return JsonResponse({
                'labels': [type_names.get(item['transaction_type'], 'Unknown') for item in data],
                'datasets': [{
                    'label': 'Transaction Count',
                    'data': [item['count'] for item in data],
                }]
            })
        
        return JsonResponse({'error': 'Invalid chart type'}, status=400)


class ExportTransactionsView(AdminRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        format_type = request.GET.get('format', 'csv')
        
        queryset = Transaction.objects.all()
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(timestamp__date__range=[start_date, end_date])
        
        if format_type == 'csv':
            return AnalyticsService.export_to_csv(queryset, filename='transactions.csv')
        elif format_type == 'excel':
            return AnalyticsService.export_to_excel(queryset, filename='transactions.xlsx')
        elif format_type == 'pdf':
            data = list(queryset.values('id', 'account__account_no', 'amount', 'transaction_type', 'timestamp'))
            return AnalyticsService.export_to_pdf(data, title='Transaction Report', filename='transactions.pdf')
        
        return JsonResponse({'error': 'Invalid format'}, status=400)


class FraudAlertsView(AdminRequiredMixin, ListView):
    model = FraudAlert
    template_name = 'admin/fraud_alerts.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        alert_type = self.request.GET.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'status_choices': FraudAlert.STATUS_CHOICES,
            'severity_choices': [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
            'alert_type_choices': FraudAlert.ALERT_TYPES,
        })
        return context


class SystemHealthView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/system_health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        redis_status = self._check_redis()
        
        celery_status = self._check_celery()
        
        db_status = self._check_database()
        
        system_metrics = self._get_system_metrics()
        
        context.update({
            'redis_status': redis_status,
            'celery_status': celery_status,
            'db_status': db_status,
            'system_metrics': system_metrics,
        })
        
        return context
    
    def _check_redis(self):
        try:
            r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            return {'status': 'healthy', 'message': 'Connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    def _check_celery(self):
        try:
            inspector = current_app.control.inspect()
            stats = inspector.stats()
            if stats:
                return {'status': 'healthy', 'message': f'{len(stats)} worker(s) active', 'workers': stats}
            return {'status': 'unhealthy', 'message': 'No workers available'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    def _check_database(self):
        try:
            User.objects.count()
            return {'status': 'healthy', 'message': 'Connected'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    def _get_system_metrics(self):
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
