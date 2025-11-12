from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(AccessMixin):
    """
    Mixin for class-based views that checks if the user is an admin.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin:
            raise PermissionDenied("You must be an admin to access this page.")
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(AccessMixin):
    """
    Mixin for class-based views that checks if the user has a specific role.
    Set required_role attribute in the view class.
    
    Example:
        class MyView(RoleRequiredMixin, TemplateView):
            required_role = 'admin'
            template_name = 'my_template.html'
    """
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.required_role is None:
            raise ValueError(
                "RoleRequiredMixin requires 'required_role' attribute to be set."
            )
        
        if not request.user.is_admin or request.user.role != self.required_role:
            raise PermissionDenied(
                f"You must have the '{self.required_role}' role to access this page."
            )
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(AccessMixin):
    """
    Custom permission mixin that works with our admin system.
    Set permission_required attribute in the view class (can be string or list).
    """
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.permission_required is None:
            raise ValueError(
                "PermissionRequiredMixin requires 'permission_required' attribute."
            )
        
        perms = (
            [self.permission_required]
            if isinstance(self.permission_required, str)
            else self.permission_required
        )
        
        if not request.user.has_perms(perms):
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)
