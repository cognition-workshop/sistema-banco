from rest_framework import viewsets, permissions
from django.core.cache import cache

from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'account', 
            'account__user', 
            'account__account_type'
        ).all()
        
        account_id = self.request.query_params.get('account_id')
        if account_id:
            cache_key = f'transactions_account_{account_id}'
            cached_data = cache.get(cache_key)
            if cached_data is None:
                queryset = queryset.filter(account_id=account_id)
                cache.set(cache_key, list(queryset), timeout=300)
            else:
                queryset = cached_data
        
        return queryset
