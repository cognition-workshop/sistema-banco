from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import UserBankAccount, BankAccountType, UserAddress
from .serializers import (
    UserSerializer,
    UserBankAccountSerializer,
    BankAccountTypeSerializer,
    UserAddressSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class UserBankAccountViewSet(viewsets.ModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type').all()
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserBankAccount.objects.select_related('user', 'account_type').all()
        return UserBankAccount.objects.filter(user=self.request.user).select_related('account_type')


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserAddressViewSet(viewsets.ModelViewSet):
    queryset = UserAddress.objects.select_related('user').all()
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserAddress.objects.select_related('user').all()
        return UserAddress.objects.filter(user=self.request.user)
