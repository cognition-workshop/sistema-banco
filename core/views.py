import logging
from django.http import JsonResponse
from django.db import connection
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/index.html"


class HealthDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/health_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def check_database(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {'status': 'healthy', 'message': 'Database connection successful'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}
    
    def check_redis(self):
        try:
            cache.set('health_check', 'ok', 10)
            value = cache.get('health_check')
            if value == 'ok':
                return {'status': 'healthy', 'message': 'Redis connection successful'}
            return {'status': 'unhealthy', 'message': 'Redis read/write failed'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Redis error: {str(e)}'}
    
    def check_celery(self):
        try:
            from celery import Celery
            app = Celery('banking_system')
            app.config_from_object('django.conf:settings', namespace='CELERY')
            
            inspect = app.control.inspect()
            active = inspect.active()
            
            if active:
                worker_count = len(active.keys())
                return {'status': 'healthy', 'message': f'{worker_count} Celery worker(s) active'}
            return {'status': 'warning', 'message': 'No Celery workers found'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Celery error: {str(e)}'}
    
    def get_system_metrics(self):
        from accounts.models import User
        from transactions.models import Transaction
        
        metrics = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_transactions': Transaction.objects.count(),
        }
        return metrics
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['database'] = self.check_database()
        context['redis'] = self.check_redis()
        context['celery'] = self.check_celery()
        context['metrics'] = self.get_system_metrics()
        
        statuses = [context['database']['status'], context['redis']['status'], context['celery']['status']]
        if all(s == 'healthy' for s in statuses):
            context['overall_status'] = 'healthy'
        elif any(s == 'unhealthy' for s in statuses):
            context['overall_status'] = 'unhealthy'
        else:
            context['overall_status'] = 'warning'
        
        return context


class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/analytics_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Avg
        from accounts.models import User, UserBankAccount
        from transactions.models import Transaction
        from transactions.constants import DEPOSIT, WITHDRAWAL
        from datetime import timedelta
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['inactive_users'] = User.objects.filter(is_active=False).count()
        
        context['total_accounts'] = UserBankAccount.objects.count()
        context['total_balance'] = UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0
        context['avg_balance'] = UserBankAccount.objects.aggregate(Avg('balance'))['balance__avg'] or 0
        
        transactions = Transaction.objects.all()
        context['total_transactions'] = transactions.count()
        context['total_deposits'] = transactions.filter(transaction_type=DEPOSIT).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_withdrawals'] = transactions.filter(transaction_type=WITHDRAWAL).aggregate(Sum('amount'))['amount__sum'] or 0
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = transactions.filter(timestamp__gte=thirty_days_ago)
        context['recent_transaction_count'] = recent_transactions.count()
        
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {'deposits': 0, 'withdrawals': 0, 'count': 0})
        
        for trans in recent_transactions:
            date_str = trans.timestamp.strftime('%Y-%m-%d')
            if trans.transaction_type == DEPOSIT:
                daily_stats[date_str]['deposits'] += float(trans.amount)
            elif trans.transaction_type == WITHDRAWAL:
                daily_stats[date_str]['withdrawals'] += float(trans.amount)
            daily_stats[date_str]['count'] += 1
        
        chart_dates = sorted(daily_stats.keys())
        chart_transaction_counts = [daily_stats[d]['count'] for d in chart_dates]
        
        context['chart_dates'] = chart_dates
        context['chart_transaction_counts'] = chart_transaction_counts
        
        return context


class AnalyticsExportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request, *args, **kwargs):
        import csv
        from django.http import HttpResponse
        from accounts.models import User, UserBankAccount
        from transactions.models import Transaction
        
        export_type = request.GET.get('type', 'transactions')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'
        
        writer = csv.writer(response)
        
        if export_type == 'transactions':
            writer.writerow(['Date', 'Account Number', 'User Email', 'Type', 'Amount', 'Balance After'])
            transactions = Transaction.objects.select_related('account__user').order_by('-timestamp')[:1000]
            for trans in transactions:
                writer.writerow([
                    trans.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    trans.account.account_no,
                    trans.account.user.email,
                    trans.get_transaction_type_display(),
                    trans.amount,
                    trans.balance_after_transaction
                ])
        
        elif export_type == 'users':
            writer.writerow(['Email', 'First Name', 'Last Name', 'Is Active', 'Date Joined', 'Account Number', 'Balance'])
            users = User.objects.select_related('account').all()
            for user in users:
                account_no = user.account.account_no if hasattr(user, 'account') else 'N/A'
                balance = user.account.balance if hasattr(user, 'account') else 0
                writer.writerow([
                    user.email,
                    user.first_name,
                    user.last_name,
                    'Yes' if user.is_active else 'No',
                    user.date_joined.strftime('%Y-%m-%d'),
                    account_no,
                    balance
                ])
        
        elif export_type == 'accounts':
            writer.writerow(['Account Number', 'User Email', 'Account Type', 'Balance', 'Initial Deposit Date'])
            accounts = UserBankAccount.objects.select_related('user', 'account_type').all()
            for account in accounts:
                writer.writerow([
                    account.account_no,
                    account.user.email,
                    account.account_type.name,
                    account.balance,
                    account.initial_deposit_date.strftime('%Y-%m-%d') if account.initial_deposit_date else 'N/A'
                ])
        
        return response


def health_check(request):
    """Health check endpoint for monitoring."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "healthy",
                "database": "ok",
            }
        )
    except Exception as e:
        logger.exception("Health check failed")
        return JsonResponse(
            {"status": "unhealthy", "database": "error", "error": str(e)}, status=503
        )
