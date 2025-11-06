from django.core.cache import cache
from .models import BankAccountType


def get_cached_account_types():
    cache_key = 'account_types'
    account_types = cache.get(cache_key)
    if account_types is None:
        account_types = list(BankAccountType.objects.all())
        cache.set(cache_key, account_types, timeout=3600)
    return account_types
