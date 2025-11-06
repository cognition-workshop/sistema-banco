from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView, View
from .health_checks import HealthCheck


class HealthDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'monitoring/health_dashboard.html'
    permission_required = 'accounts.view_user'


class HealthCheckAPIView(View):
    
    def get(self, request):
        db_status = HealthCheck.check_database()
        redis_status = HealthCheck.check_redis()
        transaction_rate = HealthCheck.check_transaction_rate()
        
        overall_status = 'healthy'
        if any(check['status'] == 'unhealthy' for check in [db_status, redis_status, transaction_rate]):
            overall_status = 'unhealthy'
        elif any(check['status'] == 'warning' for check in [db_status, redis_status, transaction_rate]):
            overall_status = 'warning'
        
        return JsonResponse({
            'status': overall_status,
            'checks': {
                'database': db_status,
                'redis': redis_status,
                'transaction_rate': transaction_rate,
            }
        })


class SystemMetricsAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'accounts.view_user'
    
    def get(self, request):
        metrics = HealthCheck.get_system_metrics()
        return JsonResponse(metrics)
