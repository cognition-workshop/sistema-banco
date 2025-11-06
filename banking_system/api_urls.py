from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from accounts.api_views import (
    BankAccountTypeViewSet, UserRegistrationAPIView, 
    UserViewSet, UserBankAccountViewSet
)
from transactions.api_views import (
    TransactionViewSet, DepositAPIView, WithdrawAPIView
)

router = DefaultRouter()
router.register(r'account-types', BankAccountTypeViewSet, basename='account-type')
router.register(r'users', UserViewSet, basename='user')
router.register(r'bank-accounts', UserBankAccountViewSet, basename='bank-account')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'),
    path('deposit/', DepositAPIView.as_view(), name='deposit'),
    path('withdraw/', WithdrawAPIView.as_view(), name='withdraw'),
]
