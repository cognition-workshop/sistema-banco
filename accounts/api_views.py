from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import UserBankAccountSerializer


class BalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'account'):
            return Response({'error': 'No bank account found for user'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserBankAccountSerializer(request.user.account)
        return Response(serializer.data)
