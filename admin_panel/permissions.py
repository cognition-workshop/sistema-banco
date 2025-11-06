from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_user') and 
                request.user.admin_user.is_admin_active)


class IsSeniorAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_user') and 
                request.user.admin_user.is_admin_active and
                request.user.admin_user.role == 'SENIOR')


class IsOperationalOrSeniorAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_user') and 
                request.user.admin_user.is_admin_active and
                request.user.admin_user.role in ['SENIOR', 'OPERATIONAL'])
