from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import UserBankAccount
from .serializers import UserBankAccountSerializer


class AccountBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        account = get_object_or_404(UserBankAccount, user=request.user)
        
        serializer = UserBankAccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)
