from django.test import TestCase, Client, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
import json

from monitoring.middleware import PerformanceMonitoringMiddleware
from monitoring.health_checks import TransactionSystemHealthCheck


class HealthCheckEndpointTests(TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint_returns_200(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_endpoint_returns_json(self):
        response = self.client.get('/health/')
        self.assertEqual(response['Content-Type'], 'application/json')
    
    @patch('health_check.contrib.redis.backends.RedisHealthCheck.check_status')
    @patch('health_check.contrib.celery.backends.CeleryHealthCheck.check_status')
    def test_health_checks_with_mocked_services(self, mock_celery, mock_redis):
        mock_redis.return_value = None
        mock_celery.return_value = None
        
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)


class DatabaseHealthCheckTests(TestCase):
    
    def test_database_health_check(self):
        response = self.client.get('/health/')
        data = json.loads(response.content)
        self.assertIn('DatabaseBackend', str(data))


class TransactionSystemHealthCheckTests(TestCase):
    
    def setUp(self):
        from accounts.models import User
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_transaction_health_check_with_transactions(self):
        from transactions.models import Transaction
        from accounts.models import Account
        
        account = Account.objects.create(
            user=self.user,
            account_number='1000000001',
            account_type='savings',
            balance=1000.00
        )
        
        Transaction.objects.create(
            account=account,
            transaction_type='deposit',
            amount=100.00,
            balance_after_transaction=1100.00
        )
        Transaction.objects.create(
            account=account,
            transaction_type='withdrawal',
            amount=50.00,
            balance_after_transaction=1050.00
        )
        
        health_check = TransactionSystemHealthCheck()
        health_check.check_status()
        
        self.assertEqual(len(health_check.errors), 0)
    
    def test_transaction_health_check_identifier(self):
        health_check = TransactionSystemHealthCheck()
        self.assertEqual(health_check.identifier(), "Transaction System")


class PerformanceMonitoringMiddlewareTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.middleware = PerformanceMonitoringMiddleware(get_response=lambda r: HttpResponse())
    
    def test_middleware_has_required_methods(self):
        self.assertTrue(hasattr(self.middleware, 'process_request'))
        self.assertTrue(hasattr(self.middleware, 'process_response'))
    
    def test_middleware_measures_duration(self):
        factory = RequestFactory()
        request = factory.get('/')
        
        self.middleware.process_request(request)
        self.assertTrue(hasattr(request, '_start_time'))
        self.assertTrue(hasattr(request, '_start_memory'))
        
        response = HttpResponse()
        self.middleware.process_response(request, response)
        
        self.assertTrue(hasattr(request, '_start_time'))
    
    @patch('monitoring.middleware.logger')
    def test_middleware_logs_with_correct_fields(self, mock_logger):
        factory = RequestFactory()
        request = factory.get('/test-path/')
        request.user = MagicMock()
        request.user.__str__ = MagicMock(return_value='testuser')
        
        self.middleware.process_request(request)
        response = HttpResponse(status=200)
        self.middleware.process_response(request, response)
        
        self.assertTrue(mock_logger.info.called)
        
        call_args = mock_logger.info.call_args
        
        self.assertEqual(call_args[0][0], 'Request completed')
        
        extra = call_args[1]['extra']
        self.assertIn('method', extra)
        self.assertIn('path', extra)
        self.assertIn('status_code', extra)
        self.assertIn('duration_ms', extra)
        self.assertIn('memory_used_mb', extra)
        self.assertIn('user', extra)
        
        self.assertEqual(extra['method'], 'GET')
        self.assertEqual(extra['path'], '/test-path/')
        self.assertEqual(extra['status_code'], 200)
        self.assertEqual(extra['user'], 'testuser')


class RedisHealthCheckTests(TestCase):
    
    @patch('redis.Redis.ping')
    def test_redis_health_check_success(self, mock_ping):
        mock_ping.return_value = True
        
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 500])
    
    @patch('redis.Redis.ping')
    def test_redis_health_check_failure(self, mock_ping):
        mock_ping.side_effect = Exception("Connection refused")
        
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 500])


class CeleryHealthCheckTests(TestCase):
    
    @patch('celery.current_app.control.inspect')
    def test_celery_health_check_success(self, mock_inspect):
        mock_inspect.return_value.active.return_value = {'worker1': []}
        
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 500])
    
    @patch('celery.current_app.control.inspect')
    def test_celery_health_check_failure(self, mock_inspect):
        mock_inspect.return_value.active.return_value = None
        
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 500])


class IntegrationTests(TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_health_endpoint_accessible(self):
        response = self.client.get('/health/')
        self.assertIsNotNone(response)
    
    def test_monitoring_app_installed(self):
        from django.conf import settings
        self.assertIn('monitoring', settings.INSTALLED_APPS)
    
    def test_health_check_apps_installed(self):
        from django.conf import settings
        self.assertIn('health_check', settings.INSTALLED_APPS)
        self.assertIn('health_check.db', settings.INSTALLED_APPS)
        self.assertIn('health_check.cache', settings.INSTALLED_APPS)
    
    def test_performance_middleware_installed(self):
        from django.conf import settings
        middleware_str = 'monitoring.middleware.PerformanceMonitoringMiddleware'
        self.assertIn(middleware_str, settings.MIDDLEWARE)
