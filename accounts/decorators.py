from functools import wraps
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is an admin.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_admin,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def role_required(role, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user has a specific role.
    Usage: @role_required('admin')
    """
    def check_role(user):
        return user.is_authenticated and user.is_admin and user.role == role
    
    actual_decorator = user_passes_test(
        check_role,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    return actual_decorator


def permission_required_custom(perm, raise_exception=False):
    """
    Custom permission decorator that works with our admin system.
    Usage: @permission_required_custom('accounts.view_user')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if not request.user.has_perm(perm):
                if raise_exception:
                    raise PermissionDenied
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
