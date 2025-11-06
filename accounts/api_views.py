from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache

from .models import BankAccountType, UserBankAccount, UserAddress
from .serializers import (
    BankAccountTypeSerializer, 
    UserBankAccountSerializer,
    UserBankAccountDetailSerializer,
    UserAddressSerializer
)


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type').all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserBankAccountDetailSerializer
        return UserBankAccountSerializer
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        account = self.get_object()
        cache_key = f'account_balance_{account.id}'
        balance = cache.get(cache_key)
        
        if balance is None:
            balance = account.balance
            cache.set(cache_key, balance, timeout=60)
        
        return Response({'balance': balance})


class UserAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserAddress.objects.select_related('user').all()
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
