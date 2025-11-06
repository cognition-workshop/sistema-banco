from django.shortcuts import redirect
from django.urls import reverse
from .models import AdminAuditLog


class AdminPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/admin-portal/'):
            if request.path == reverse('admin_panel:login'):
                response = self.get_response(request)
                return response
            
            if not request.user.is_authenticated:
                return redirect('admin_panel:login')
            
            if not hasattr(request.user, 'role'):
                return redirect('home')
            
            if request.user.role == 'REGULAR_USER':
                return redirect('home')
            
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                AdminAuditLog.objects.create(
                    user=request.user,
                    action=f"{request.method} {request.path}",
                    ip_address=self.get_client_ip(request)
                )
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
