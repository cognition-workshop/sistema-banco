from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .models import BankAccountType, UserBankAccount, UserAddress
from .serializers import (
    UserSerializer, 
    BankAccountTypeSerializer, 
    UserBankAccountSerializer,
    UserAddressSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BankAccountTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BankAccountType.objects.all()
    serializer_class = BankAccountTypeSerializer


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserBankAccount.objects.select_related('user', 'account_type').all()
    serializer_class = UserBankAccountSerializer


class UserAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserAddress.objects.select_related('user').all()
    serializer_class = UserAddressSerializer
