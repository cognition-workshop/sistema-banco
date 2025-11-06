from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.api_views import (
    UserViewSet,
    UserBankAccountViewSet,
    BankAccountTypeViewSet,
    UserAddressViewSet
)
from transactions.api_views import TransactionViewSet
from pix.api_views import PixKeyViewSet, PixTransferViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'bank-accounts', UserBankAccountViewSet, basename='account')
router.register(r'account-types', BankAccountTypeViewSet, basename='accounttype')
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'pix-keys', PixKeyViewSet, basename='pixkey')
router.register(r'pix-transfer', PixTransferViewSet, basename='pixtransfer')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
