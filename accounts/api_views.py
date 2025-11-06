from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, UserBankAccount, UserAddress, BankAccountType
from .serializers import (UserSerializer, UserBankAccountSerializer, 
                          UserAddressSerializer, BankAccountTypeSerializer)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def account(self, request, pk=None):
        user = self.get_object()
        if hasattr(user, 'account'):
            serializer = UserBankAccountSerializer(user.account)
            return Response(serializer.data)
        return Response({'detail': 'No account found'}, status=404)


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type')
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)


class UserAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserAddress.objects.select_related('user')
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)
