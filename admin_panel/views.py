from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, UpdateView
from datetime import timedelta

from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from .forms import UserSearchForm, UserEditForm, UserSuspendForm


class AdminDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    permission_required = 'accounts.view_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['total_accounts'] = UserBankAccount.objects.count()
        context['total_balance'] = UserBankAccount.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        last_24h = timezone.now() - timedelta(hours=24)
        context['transactions_24h'] = Transaction.objects.filter(
            timestamp__gte=last_24h
        ).count()
        
        context['recent_transactions'] = Transaction.objects.select_related(
            'account__user'
        ).order_by('-timestamp')[:10]
        
        return context


class UserManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'admin_panel/user_management.html'
    model = User
    permission_required = 'accounts.view_user'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.select_related('account').all()
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(account__account_no__icontains=search_query)
            )
        
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserSearchForm(self.request.GET)
        return context


class UserEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    template_name = 'admin_panel/user_edit.html'
    model = User
    form_class = UserEditForm
    permission_required = 'accounts.change_user'
    success_url = reverse_lazy('admin_panel:user_management')
    
    def form_valid(self, form):
        messages.success(self.request, f'Usuário {form.instance.email} atualizado com sucesso!')
        return super().form_valid(form)


def suspend_user(request, pk):
    if not request.user.has_perm('accounts.change_user'):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('admin_panel:user_management')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    
    from .models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action='suspend_user',
        target_user=user,
        description=f'Usuário {user.email} foi suspenso'
    )
    
    messages.success(request, f'Usuário {user.email} foi suspenso.')
    return redirect('admin_panel:user_management')


def reactivate_user(request, pk):
    if not request.user.has_perm('accounts.change_user'):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('admin_panel:user_management')
    
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    
    from .models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action='reactivate_user',
        target_user=user,
        description=f'Usuário {user.email} foi reativado'
    )
    
    messages.success(request, f'Usuário {user.email} foi reativado.')
    return redirect('admin_panel:user_management')


class TransactionMonitorView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'admin_panel/transaction_monitor.html'
    model = Transaction
    permission_required = 'transactions.view_transaction'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'account__user'
        ).all()
        
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        transaction_type = self.request.GET.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        user_search = self.request.GET.get('user_search')
        if user_search:
            queryset = queryset.filter(
                Q(account__user__email__icontains=user_search) |
                Q(account__account_no__icontains=user_search)
            )
        
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from transactions.constants import TRANSACTION_TYPE_CHOICES
        context['transaction_types'] = TRANSACTION_TYPE_CHOICES
        return context
