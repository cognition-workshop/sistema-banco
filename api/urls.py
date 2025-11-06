from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from .viewsets import UserViewSet, UserBankAccountViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', UserBankAccountViewSet, basename='account')
router.register(r'transactions', TransactionViewSet, basename='transaction')

app_name = 'api'

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
