from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .models import UserBankAccount
from .serializers import UserSerializer, UserBankAccountSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class UserBankAccountViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserBankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserBankAccount.objects.filter(user=self.request.user)
