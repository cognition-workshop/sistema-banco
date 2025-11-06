from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from accounts.viewsets import (
    UserViewSet, UserBankAccountViewSet, 
    BankAccountTypeViewSet, UserAddressViewSet
)
from transactions.viewsets import TransactionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', UserBankAccountViewSet, basename='account')
router.register(r'account-types', BankAccountTypeViewSet, basename='account-type')
router.register(r'addresses', UserAddressViewSet, basename='address')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
