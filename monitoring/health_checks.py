from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
import time


class HealthCheck:
    
    @staticmethod
    def check_database():
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'message': 'Conexão com banco de dados OK'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': 0,
                'message': f'Erro na conexão com banco de dados: {str(e)}'
            }
    
    @staticmethod
    def check_redis():
        try:
            start_time = time.time()
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            response_time = (time.time() - start_time) * 1000
            
            if result == 'ok':
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time, 2),
                    'message': 'Conexão com Redis OK'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time_ms': 0,
                    'message': 'Redis não respondeu corretamente'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time_ms': 0,
                'message': f'Erro na conexão com Redis: {str(e)}'
            }
    
    @staticmethod
    def check_transaction_rate():
        from transactions.models import Transaction
        from datetime import timedelta
        
        try:
            one_minute_ago = timezone.now() - timedelta(minutes=1)
            count = Transaction.objects.filter(
                timestamp__gte=one_minute_ago
            ).count()
            
            status = 'healthy' if count < 1000 else 'warning'
            
            return {
                'status': status,
                'transactions_per_minute': count,
                'message': f'{count} transações no último minuto'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'transactions_per_minute': 0,
                'message': f'Erro ao verificar transações: {str(e)}'
            }
    
    @staticmethod
    def get_system_metrics():
        from accounts.models import User, UserBankAccount
        from transactions.models import Transaction
        from django.db.models import Avg, Sum
        from datetime import timedelta
        
        try:
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            recent_transactions = Transaction.objects.filter(
                timestamp__gte=one_hour_ago
            )
            
            metrics = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'total_accounts': UserBankAccount.objects.count(),
                'transactions_last_hour': recent_transactions.count(),
                'total_balance': float(
                    UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0
                ),
                'timestamp': timezone.now().isoformat(),
            }
            
            return metrics
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat(),
            }
