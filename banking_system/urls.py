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
from rest_framework import routers

from core.views import HomeView
from accounts.viewsets import (
    UserViewSet,
    BankAccountTypeViewSet,
    UserBankAccountViewSet,
    UserAddressViewSet,
)
from transactions.viewsets import TransactionViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'account-types', BankAccountTypeViewSet)
router.register(r'bank-accounts', UserBankAccountViewSet)
router.register(r'addresses', UserAddressViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path(
        'transactions/',
        include('transactions.urls', namespace='transactions')
    )
]
