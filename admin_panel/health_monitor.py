import psutil
import time
from django.db import connection
from django.core.cache import cache
from celery import current_app


class HealthMonitor:
    
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self):
        memory = psutil.virtual_memory()
        return {
            'percent': memory.percent,
            'used': memory.used,
            'total': memory.total,
            'available': memory.available
        }
    
    def get_network_stats(self):
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    def get_db_response_time(self):
        start = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return (time.time() - start) * 1000
        except Exception as e:
            return -1
    
    def get_redis_status(self):
        try:
            cache.set('health_check', 'ok', 1)
            result = cache.get('health_check')
            return result == 'ok'
        except Exception:
            return False
    
    def get_celery_status(self):
        try:
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            return bool(stats)
        except Exception:
            return False
    
    def get_all_metrics(self):
        cpu = self.get_cpu_usage()
        memory = self.get_memory_usage()
        network = self.get_network_stats()
        db_response = self.get_db_response_time()
        redis_status = self.get_redis_status()
        celery_status = self.get_celery_status()
        
        return {
            'cpu': {
                'usage_percent': cpu,
                'status': 'HEALTHY' if cpu < 80 else 'WARNING' if cpu < 95 else 'CRITICAL'
            },
            'memory': {
                'usage_percent': memory['percent'],
                'used_mb': memory['used'] / (1024 * 1024),
                'total_mb': memory['total'] / (1024 * 1024),
                'status': 'HEALTHY' if memory['percent'] < 80 else 'WARNING' if memory['percent'] < 95 else 'CRITICAL'
            },
            'network': {
                'bytes_sent_mb': network['bytes_sent'] / (1024 * 1024),
                'bytes_recv_mb': network['bytes_recv'] / (1024 * 1024),
                'status': 'HEALTHY'
            },
            'database': {
                'response_time_ms': db_response,
                'status': 'HEALTHY' if 0 < db_response < 100 else 'WARNING' if db_response < 500 else 'CRITICAL'
            },
            'redis': {
                'is_available': redis_status,
                'status': 'HEALTHY' if redis_status else 'CRITICAL'
            },
            'celery': {
                'is_available': celery_status,
                'status': 'HEALTHY' if celery_status else 'WARNING'
            }
        }
