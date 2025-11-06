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
from accounts import admin_views


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/analytics/', admin_views.analytics_dashboard, name='admin_analytics'),
    path('admin/fraud-detection/', admin_views.fraud_detection_dashboard, name='admin_fraud_detection'),
    path('admin/system-health/', admin_views.system_health_dashboard, name='admin_system_health'),
    path('admin/', admin.site.urls),
    path(
        'transactions/',
        include('transactions.urls', namespace='transactions')
    )
]
