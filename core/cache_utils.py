from django.core.cache import cache
from functools import wraps


def get_balance_cache_key(user_id):
    """Generate cache key for user balance."""
    return f'balance:user:{user_id}'


def get_account_cache_key(account_id):
    """Generate cache key for account details."""
    return f'account:{account_id}'


def get_transactions_cache_key(account_id, daterange=None):
    """Generate cache key for transaction list."""
    if daterange:
        return f'transactions:account:{account_id}:range:{daterange[0]}:{daterange[1]}'
    return f'transactions:account:{account_id}:all'


def get_account_type_cache_key(account_type_id):
    """Generate cache key for account type."""
    return f'account_type:{account_type_id}'


def invalidate_balance_cache(user_id):
    """Invalidate balance cache for a user."""
    cache_key = get_balance_cache_key(user_id)
    cache.delete(cache_key)


def invalidate_account_cache(account_id):
    """Invalidate account cache."""
    cache_key = get_account_cache_key(account_id)
    cache.delete(cache_key)


def invalidate_transactions_cache(account_id):
    """Invalidate all transaction caches for an account."""
    pattern = f'banking:transactions:account:{account_id}:*'
    cache.delete_pattern(pattern)


def cache_account_type(timeout=3600):
    """Decorator to cache account type data (1 hour default)."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = get_account_type_cache_key(self.id)
            result = cache.get(cache_key)
            if result is None:
                result = func(self, *args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
