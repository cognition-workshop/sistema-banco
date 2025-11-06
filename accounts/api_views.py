from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import BalanceSerializer


class BalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = BalanceSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
