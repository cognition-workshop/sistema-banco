from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import admin_required, permission_required
from accounts.models import VIEW_USERS, EDIT_USERS
from .filters import UserFilter

User = get_user_model()


@method_decorator(admin_required, name='dispatch')
@method_decorator(permission_required(VIEW_USERS), name='dispatch')
class UserManagementView(ListView):
    model = User
    template_name = 'admin/user_management.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = User.objects.select_related('account', 'address').all()
        
        self.filterset = UserFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['can_edit'] = EDIT_USERS in self.request.user.admin_permissions
        return context


@admin_required
@permission_required(EDIT_USERS)
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:user_management')
    
    if user.is_superuser:
        messages.error(request, 'You cannot deactivate superuser accounts.')
        return redirect('accounts:user_management')
    
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.email} has been {status}.')
    
    return redirect('accounts:user_management')
