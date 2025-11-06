from django.test import TestCase
from admin_panel.health_monitor import HealthMonitor


class HealthMonitorTest(TestCase):
    
    def setUp(self):
        self.monitor = HealthMonitor()
    
    def test_get_cpu_usage(self):
        cpu_usage = self.monitor.get_cpu_usage()
        self.assertIsInstance(cpu_usage, float)
        self.assertGreaterEqual(cpu_usage, 0)
        self.assertLessEqual(cpu_usage, 100)
    
    def test_get_memory_usage(self):
        memory = self.monitor.get_memory_usage()
        self.assertIsInstance(memory, dict)
        self.assertIn('percent', memory)
        self.assertIn('used', memory)
        self.assertIn('total', memory)
    
    def test_get_network_stats(self):
        network = self.monitor.get_network_stats()
        self.assertIsInstance(network, dict)
        self.assertIn('bytes_sent', network)
        self.assertIn('bytes_recv', network)
    
    def test_get_db_response_time(self):
        response_time = self.monitor.get_db_response_time()
        self.assertIsInstance(response_time, float)
        self.assertGreater(response_time, 0)
    
    def test_get_all_metrics(self):
        metrics = self.monitor.get_all_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('cpu', metrics)
        self.assertIn('memory', metrics)
        self.assertIn('database', metrics)
