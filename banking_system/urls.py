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
from transactions.admin_views import (
    transaction_dashboard,
    analytics_dashboard,
    system_health_dashboard
)

admin.site.site_header = 'Sistema Bancário - Administração'
admin.site.site_title = 'Admin Sistema Bancário'
admin.site.index_title = 'Painel Administrativo'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/dashboards/transactions/', transaction_dashboard, name='admin_transaction_dashboard'),
    path('admin/dashboards/analytics/', analytics_dashboard, name='admin_analytics_dashboard'),
    path('admin/dashboards/system-health/', system_health_dashboard, name='admin_system_health'),
    path('admin/', admin.site.urls),
    path(
        'transactions/',
        include('transactions.urls', namespace='transactions')
    )
]
