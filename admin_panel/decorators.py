from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access admin panel')
            return redirect('accounts:user_login')
        
        if not hasattr(request.user, 'admin_profile'):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access admin panel')
            return redirect('accounts:user_login')
        
        if not hasattr(request.user, 'admin_profile'):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)
