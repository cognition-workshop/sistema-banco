from django.test import TestCase, Client
from django.urls import reverse


class HealthCheckTests(TestCase):
    """Test health check endpoint."""

    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200(self):
        """Test that health check endpoint returns 200."""
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertEqual(response.json()["database"], "ok")
