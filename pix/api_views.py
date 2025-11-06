from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .models import PixKey
from .serializers import PixKeySerializer, PixTransferSerializer
from transactions.models import Transaction
from transactions.constants import PIX_TRANSFER


class PixKeyViewSet(viewsets.ModelViewSet):
    queryset = PixKey.objects.select_related('account__user').all()
    serializer_class = PixKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return PixKey.objects.select_related('account__user').all()
        if hasattr(self.request.user, 'account'):
            return PixKey.objects.filter(
                account=self.request.user.account,
                is_active=True
            ).select_related('account__user')
        return PixKey.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'account'):
            serializer.save(account=self.request.user.account)


class PixTransferViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def transfer(self, request):
        serializer = PixTransferSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            pix_key = serializer.context.get('pix_key_obj')
            sender_account = request.user.account
            receiver_account = pix_key.account

            with transaction.atomic():
                sender_account.balance -= amount
                sender_account.save(update_fields=['balance'])

                receiver_account.balance += amount
                receiver_account.save(update_fields=['balance'])

                sender_transaction = Transaction.objects.create(
                    account=sender_account,
                    amount=-amount,
                    balance_after_transaction=sender_account.balance,
                    transaction_type=PIX_TRANSFER
                )

                receiver_transaction = Transaction.objects.create(
                    account=receiver_account,
                    amount=amount,
                    balance_after_transaction=receiver_account.balance,
                    transaction_type=PIX_TRANSFER
                )

            return Response({
                'message': 'Transfer successful',
                'sender_transaction_id': sender_transaction.id,
                'receiver_transaction_id': receiver_transaction.id,
                'amount': amount,
                'new_balance': sender_account.balance
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
