from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import UserViewSet, AccountViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
