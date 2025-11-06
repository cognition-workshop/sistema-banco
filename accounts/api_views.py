from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import UserBankAccount
from .serializers import UserBankAccountSerializer


class AccountBalanceView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            account = request.user.account
        except UserBankAccount.DoesNotExist:
            return Response(
                {'error': 'Bank account not found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserBankAccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)
