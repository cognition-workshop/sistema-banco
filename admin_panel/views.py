from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

from .decorators import AdminRequiredMixin
from .models import AdminUser, FraudDetectionRule, FraudAlert
from .health_checks import check_database_health, check_redis_health, check_celery_health, get_system_metrics
from accounts.models import UserBankAccount
from transactions.models import Transaction

User = get_user_model()


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        context['total_users'] = User.objects.count()
        context['total_accounts'] = UserBankAccount.objects.count()
        context['transactions_today'] = Transaction.objects.filter(timestamp__date=today).count()
        context['pending_alerts'] = FraudAlert.objects.filter(status='pending').count()
        
        context['total_balance'] = UserBankAccount.objects.aggregate(
            total=Sum('balance'))['total'] or 0
        
        context['recent_transactions'] = Transaction.objects.select_related(
            'account__user').order_by('-timestamp')[:10]
        
        context['pending_fraud_alerts'] = FraudAlert.objects.filter(
            status='pending').select_related('transaction', 'rule')[:5]
        
        return context


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin_panel/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.select_related('account').all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search)
            )
        return queryset


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    template_name = 'admin_panel/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        if hasattr(user, 'account'):
            context['transactions'] = Transaction.objects.filter(
                account=user.account).order_by('-timestamp')[:20]
            context['fraud_alerts'] = FraudAlert.objects.filter(
                transaction__account=user.account).order_by('-created_at')[:10]
        
        return context


class TransactionListView(AdminRequiredMixin, ListView):
    model = Transaction
    template_name = 'admin_panel/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('account__user').all()
        
        transaction_type = self.request.GET.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        start_date = self.request.GET.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        
        end_date = self.request.GET.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        min_amount = self.request.GET.get('min_amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        
        return queryset.order_by('-timestamp')


class AnalyticsDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        last_30_days = timezone.now() - timedelta(days=30)
        
        context['transaction_volume'] = Transaction.objects.filter(
            timestamp__gte=last_30_days
        ).values('timestamp__date').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('timestamp__date')
        
        context['top_users'] = UserBankAccount.objects.annotate(
            transaction_count=Count('transactions')
        ).order_by('-transaction_count')[:10]
        
        context['transaction_type_stats'] = Transaction.objects.filter(
            timestamp__gte=last_30_days
        ).values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return context


class FraudRuleListView(AdminRequiredMixin, ListView):
    model = FraudDetectionRule
    template_name = 'admin_panel/fraud_rules.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        return FraudDetectionRule.objects.select_related('created_by').all()


class FraudRuleCreateView(AdminRequiredMixin, CreateView):
    model = FraudDetectionRule
    template_name = 'admin_panel/fraud_rule_form.html'
    fields = ['name', 'description', 'rule_type', 'threshold_value', 'time_window_minutes', 'is_active']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user.admin_profile
        messages.success(self.request, 'Fraud detection rule created successfully')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/admin-panel/fraud/rules/'


class FraudAlertListView(AdminRequiredMixin, ListView):
    model = FraudAlert
    template_name = 'admin_panel/fraud_alerts.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = FraudAlert.objects.select_related(
            'transaction__account__user', 'rule', 'resolved_by'
        ).all()
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class SystemHealthView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/system_health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['database_health'] = check_database_health()
        context['redis_health'] = check_redis_health()
        context['celery_health'] = check_celery_health()
        context['system_metrics'] = get_system_metrics()
        
        return context


class UserSuspendView(AdminRequiredMixin, TemplateView):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        
        status = "suspended" if not user.is_active else "activated"
        messages.success(request, f'User {user.email} has been {status}')
        
        if request.headers.get('HX-Request'):
            return render(request, 'admin_panel/partials/user_status.html', {'user': user})
        
        return redirect('admin_panel:user_detail', pk=pk)


class UserEditView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/user_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = get_object_or_404(User, pk=kwargs['pk'])
        return context
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, f'User {user.email} updated successfully')
        return redirect('admin_panel:user_detail', pk=pk)
