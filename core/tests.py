from django.test import TestCase, Client


class TestHealthChecks(TestCase):
    """Testes para health checks"""

    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """Testa endpoint de health check"""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "OK")
        self.assertIn("timestamp", data)

    def test_readiness_check_endpoint(self):
        """Testa endpoint de readiness check"""
        response = self.client.get("/readiness/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("database", data["checks"])


class TestErrorPages(TestCase):
    """Testes para páginas de erro customizadas"""

    def setUp(self):
        self.client = Client()

    def test_404_page(self):
        """Testa página 404 customizada"""
        response = self.client.get("/pagina-inexistente/")
        self.assertEqual(response.status_code, 404)


class TestHomeView(TestCase):
    """Testes para página inicial"""

    def test_home_page_loads(self):
        """Testa que página inicial carrega"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class TestCustomExceptions(TestCase):
    """Testes para exceções customizadas"""

    def test_banking_system_exception(self):
        """Testa exceção base do sistema bancário"""
        from core.exceptions import BankingSystemException

        with self.assertRaises(BankingSystemException):
            raise BankingSystemException("Test error")

    def test_insufficient_balance_exception(self):
        """Testa exceção de saldo insuficiente"""
        from core.exceptions import InsufficientBalanceException

        with self.assertRaises(InsufficientBalanceException):
            raise InsufficientBalanceException("Insufficient balance")

    def test_invalid_transaction_exception(self):
        """Testa exceção de transação inválida"""
        from core.exceptions import InvalidTransactionException

        with self.assertRaises(InvalidTransactionException):
            raise InvalidTransactionException("Invalid transaction")

    def test_account_not_found_exception(self):
        """Testa exceção de conta não encontrada"""
        from core.exceptions import AccountNotFoundException

        with self.assertRaises(AccountNotFoundException):
            raise AccountNotFoundException("Account not found")

    def test_validation_exception(self):
        """Testa exceção de validação"""
        from core.exceptions import ValidationException

        with self.assertRaises(ValidationException):
            raise ValidationException("Validation error")


class TestSafeViewDecorator(TestCase):
    """Testes para decorator @safe_view"""

    def test_safe_view_decorator_success(self):
        """Testa decorator em view que funciona normalmente"""
        from django.http import HttpResponse
        from core.decorators import safe_view

        @safe_view
        def test_view(request):
            return HttpResponse("Success")

        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")

        response = test_view(request)
        self.assertEqual(response.status_code, 200)

    def test_safe_view_decorator_handles_exception(self):
        """Testa decorator captura exceções"""
        from core.decorators import safe_view
        from unittest.mock import patch

        @safe_view
        def test_view(request):
            raise Exception("Test error")

        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")

        with patch("core.decorators.messages") as mock_messages:
            response = test_view(request)
            self.assertEqual(response.status_code, 302)
            mock_messages.error.assert_called_once()
