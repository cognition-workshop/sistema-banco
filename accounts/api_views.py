from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.serializers import AccountBalanceSerializer


class AccountBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not hasattr(request.user, 'account'):
            return Response(
                {'error': 'Account not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AccountBalanceSerializer(request.user.account)
        return Response(serializer.data)
