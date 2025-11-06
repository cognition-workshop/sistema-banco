from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserViewSet,
    BankAccountTypeViewSet,
    UserBankAccountViewSet,
    UserAddressViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'account-types', BankAccountTypeViewSet)
router.register(r'bank-accounts', UserBankAccountViewSet)
router.register(r'addresses', UserAddressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
