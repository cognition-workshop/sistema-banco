from unittest.mock import patch, Mock
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.db import OperationalError
from django.contrib.auth import get_user_model

from core.middleware import ErrorHandlingMiddleware

User = get_user_model()


class CoreAppTest(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)


class ErrorHandlingMiddlewareTestCase(TestCase):
    """Test the custom error handling middleware"""

    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=HttpResponse())
        self.middleware = ErrorHandlingMiddleware(self.get_response)
        self.user = User.objects.create_user(email="test@example.com", password="testpass123")

    def test_middleware_passes_normal_requests(self):
        """Test that middleware doesn't interfere with normal requests"""
        request = self.factory.get("/")
        request.user = self.user

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        self.get_response.assert_called_once_with(request)

    @patch("core.middleware.logger")
    def test_middleware_catches_general_exception(self, mock_logger):
        """Test that middleware catches and logs unhandled exceptions"""
        request = self.factory.get("/test/")
        request.user = self.user

        test_exception = Exception("Test exception")
        self.middleware.process_exception(request, test_exception)

        mock_logger.error.assert_called()
        call_args = str(mock_logger.error.call_args)
        self.assertIn("Unhandled exception", call_args)
        self.assertIn("test@example.com", call_args)

    @patch("core.middleware.logger")
    @patch("core.middleware.render")
    def test_middleware_handles_database_errors(self, mock_render, mock_logger):
        """Test that middleware specifically handles database errors"""
        request = self.factory.post("/test/")
        request.user = self.user

        db_exception = OperationalError("Database locked")
        self.middleware.process_exception(request, db_exception)

        mock_logger.error.assert_called()
        self.assertIn("Database error", str(mock_logger.error.call_args))
        mock_render.assert_called_once()
        render_args = mock_render.call_args
        self.assertEqual(render_args[0][1], "500.html")

    @patch("core.middleware.logger")
    def test_middleware_logs_request_context(self, mock_logger):
        """Test that middleware logs full request context"""
        request = self.factory.post("/test/", data={"key": "value"})
        request.user = self.user

        test_exception = Exception("Test exception")
        self.middleware.process_exception(request, test_exception)

        call_kwargs = mock_logger.error.call_args[1]
        extra_data = call_kwargs.get("extra", {})

        self.assertEqual(extra_data["user"], "test@example.com")
        self.assertEqual(extra_data["path"], "/test/")
        self.assertEqual(extra_data["method"], "POST")

    @patch("core.middleware.logger")
    def test_middleware_handles_anonymous_user(self, mock_logger):
        """Test that middleware handles requests from anonymous users"""
        request = self.factory.get("/test/")
        request.user = None

        test_exception = Exception("Test exception")
        self.middleware.process_exception(request, test_exception)

        mock_logger.error.assert_called()
        call_kwargs = mock_logger.error.call_args[1]
        extra_data = call_kwargs.get("extra", {})
        self.assertEqual(extra_data["user"], "Anonymous")
