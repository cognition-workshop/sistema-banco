from django.urls import path
from . import views

app_name = 'system_health'

urlpatterns = [
    path('', views.SystemHealthDashboardView.as_view(), name='dashboard'),
    path('api/database/', views.DatabaseStatusView.as_view(), name='database_status'),
    path('api/redis/', views.RedisStatusView.as_view(), name='redis_status'),
    path('api/celery/', views.CeleryStatusView.as_view(), name='celery_status'),
    path('api/metrics/', views.PerformanceMetricsView.as_view(), name='performance_metrics'),
]
