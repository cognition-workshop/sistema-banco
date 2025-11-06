from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_required(function=None, login_url=None):
    if login_url is None:
        login_url = '/admin-portal/login/'
    
    def check_admin(user):
        if not user.is_authenticated:
            return False
        return user.is_staff
    
    actual_decorator = user_passes_test(
        check_admin,
        login_url=login_url,
        redirect_field_name='next'
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator


def permission_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/admin-portal/login/')
            
            if not request.user.is_staff:
                raise PermissionDenied("You must be staff to access this resource.")
            
            if permission_name not in request.user.admin_permissions:
                raise PermissionDenied(f"You need '{permission_name}' permission to access this resource.")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
