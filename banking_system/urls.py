"""banking_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from core.views import HomeView
from core.admin_views import (
    AdminDashboardView,
    AnalyticsView,
    AnalyticsDataAPIView,
    ExportTransactionsView,
    FraudAlertsView,
    SystemHealthView,
)


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/', admin.site.urls),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin:dashboard'),
    path('admin/analytics/', AnalyticsView.as_view(), name='admin:analytics'),
    path('admin/analytics/api/', AnalyticsDataAPIView.as_view(), name='admin:analytics_api'),
    path('admin/export/', ExportTransactionsView.as_view(), name='admin:export_transactions'),
    path('admin/fraud-alerts/', FraudAlertsView.as_view(), name='admin:fraud_alerts'),
    path('admin/system-health/', SystemHealthView.as_view(), name='admin:system_health'),
    path(
        'transactions/',
        include('transactions.urls', namespace='transactions')
    )
]
