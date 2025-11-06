from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from .health_checks import run_health_checks


class HomeView(TemplateView):
    template_name = "core/index.html"


class HealthCheckView(View):
    def get(self, request):
        health_status = run_health_checks()
        status_code = 200 if health_status["status"] == "healthy" else 503
        return JsonResponse(health_status, status=status_code)
