from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions.views import TransactionViewSet
from accounts.views import UserBankAccountViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'accounts', UserBankAccountViewSet, basename='account')

urlpatterns = [
    path('', include(router.urls)),
]
