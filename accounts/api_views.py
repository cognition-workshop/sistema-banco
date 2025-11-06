from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserBankAccount
from .serializers import AccountBalanceSerializer


class AccountBalanceAPIView(generics.RetrieveAPIView):
    serializer_class = AccountBalanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        
        if not hasattr(user, 'account'):
            return None
        
        return user.account
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance is None:
            return Response(
                {'detail': 'Account not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
