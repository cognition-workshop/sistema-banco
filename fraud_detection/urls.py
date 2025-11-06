from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('', views.fraud_dashboard_view, name='dashboard'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert_view, name='resolve_alert'),
]
