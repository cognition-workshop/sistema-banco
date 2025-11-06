from rest_framework import viewsets, permissions
from django.core.cache import cache
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        cache_key = f'transactions_{user.id}'
        
        cached_transactions = cache.get(cache_key)
        if cached_transactions is not None:
            return cached_transactions
        
        queryset = Transaction.objects.filter(
            account=user.account
        ).select_related('account')
        
        cache.set(cache_key, queryset, 300)
        return queryset
