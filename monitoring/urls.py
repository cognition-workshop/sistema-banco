from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.HealthDashboardView.as_view(), name='health_dashboard'),
    path('api/health/', views.HealthCheckAPIView.as_view(), name='health_check_api'),
    path('api/metrics/', views.SystemMetricsAPIView.as_view(), name='system_metrics_api'),
]
