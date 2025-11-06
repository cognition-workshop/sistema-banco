from functools import wraps
from django.core.cache import cache


def cache_user_data(timeout=300):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if hasattr(request, 'user') and request.user.is_authenticated:
                cache_key = f'user_data_{request.user.id}_{func.__name__}'
                result = cache.get(cache_key)
                if result is None:
                    result = func(request, *args, **kwargs)
                    cache.set(cache_key, result, timeout)
                return result
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def invalidate_user_cache(user_id, func_name=None):
    if func_name:
        cache_key = f'user_data_{user_id}_{func_name}'
        cache.delete(cache_key)
    else:
        pattern = f'user_data_{user_id}_*'
        cache.delete_pattern(pattern)
