from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import UserBankAccountSerializer


class AccountBalanceView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not hasattr(user, 'account'):
            return Response(
                {'error': 'User has no associated bank account'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = UserBankAccountSerializer(user.account)
        return Response(serializer.data, status=status.HTTP_200_OK)
