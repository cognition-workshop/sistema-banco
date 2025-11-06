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


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('health/', include('health.urls', namespace='health')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('fraud-detection/', include('fraud_detection.urls', namespace='fraud_detection')),
    path('api/v1/', include('banking_system.api_urls')),
    path(
        'transactions/',
        include('transactions.urls', namespace='transactions')
    )
]
