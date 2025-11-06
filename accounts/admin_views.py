from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from accounts.models import User


@method_decorator(staff_member_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'admin/user_management.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('account', 'address')
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return qs


@staff_member_required
def toggle_user_suspension(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_suspended = not user.is_suspended
    user.save()
    status = 'suspended' if user.is_suspended else 'activated'
    messages.success(request, f'User {user.email} has been {status}')
    return redirect('accounts:admin_user_list')
