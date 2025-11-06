from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, View
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from .models import FraudAlert, FraudRule, AdminAuditLog, AccountWhitelist
from .forms import AdminLoginForm, UserSearchForm, UserEditForm, TransactionFilterForm, FraudAlertForm
from .utils import (
    export_users_csv, export_transactions_csv, export_analytics_pdf,
    get_system_health, calculate_kpis, detect_suspicious_transactions
)


class AdminLoginView(View):
    template_name = 'admin_panel/login.html'
    
    def get(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role != 'REGULAR_USER':
            return redirect('admin_panel:dashboard')
        form = AdminLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = AdminLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'role') and user.role != 'REGULAR_USER':
                login(request, user)
                AdminAuditLog.objects.create(
                    user=user,
                    action='Admin Login',
                    ip_address=self.get_client_ip(request)
                )
                return redirect('admin_panel:dashboard')
            else:
                messages.error(request, 'You do not have admin privileges.')
        return render(request, self.template_name, {'form': form})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class AdminLogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            AdminAuditLog.objects.create(
                user=request.user,
                action='Admin Logout',
                ip_address=self.get_client_ip(request)
            )
            logout(request)
        return redirect('admin_panel:login')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    login_url = 'admin_panel:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_accounts'] = UserBankAccount.objects.count()
        context['total_transactions'] = Transaction.objects.count()
        context['pending_alerts'] = FraudAlert.objects.filter(status='PENDING').count()
        context['system_health'] = get_system_health()
        return context


class UsersDashboardView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'admin_panel/users_dashboard.html'
    context_object_name = 'users'
    paginate_by = 25
    login_url = 'admin_panel:login'
    
    def get_queryset(self):
        queryset = User.objects.select_related('account', 'account__account_type').all()
        
        form = UserSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(email__icontains=search) | 
                    Q(account__account_no__icontains=search)
                )
            
            status = form.cleaned_data.get('account_status')
            if status == 'suspended':
                queryset = queryset.filter(account__conta_suspensa=True)
            elif status == 'pending':
                queryset = queryset.filter(account__verificacao_pendente=True)
            elif status == 'high_risk':
                queryset = queryset.filter(account__alto_risco=True)
            elif status == 'active':
                queryset = queryset.filter(
                    account__conta_suspensa=False,
                    account__verificacao_pendente=False
                )
            
            balance_min = form.cleaned_data.get('balance_min')
            if balance_min:
                queryset = queryset.filter(account__balance__gte=balance_min)
            
            balance_max = form.cleaned_data.get('balance_max')
            if balance_max:
                queryset = queryset.filter(account__balance__lte=balance_max)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UserSearchForm(self.request.GET)
        context['total_count'] = self.get_queryset().count()
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'admin_panel/user_detail.html'
    context_object_name = 'user_obj'
    login_url = 'admin_panel:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        if hasattr(user, 'account'):
            context['transactions'] = Transaction.objects.filter(
                account=user.account
            ).order_by('-timestamp')[:20]
            context['fraud_alerts'] = FraudAlert.objects.filter(
                account=user.account
            ).order_by('-created_at')[:10]
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'admin_panel/user_edit.html'
    login_url = 'admin_panel:login'
    
    def get_success_url(self):
        return reverse_lazy('admin_panel:user_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        AdminAuditLog.objects.create(
            user=self.request.user,
            action=f'Updated user {form.instance.email}',
            target_model='User',
            target_id=form.instance.id,
            ip_address=self.get_client_ip(self.request)
        )
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class UserBulkActionView(LoginRequiredMixin, View):
    login_url = 'admin_panel:login'
    
    def post(self, request):
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')
        
        if not user_ids:
            messages.error(request, 'No users selected.')
            return redirect('admin_panel:users_dashboard')
        
        accounts = UserBankAccount.objects.filter(user_id__in=user_ids)
        
        if action == 'suspend':
            accounts.update(conta_suspensa=True)
            AdminAuditLog.objects.create(
                user=request.user,
                action=f'Suspended {len(user_ids)} accounts',
                ip_address=self.get_client_ip(request)
            )
            messages.success(request, f'Successfully suspended {len(user_ids)} accounts.')
        elif action == 'reactivate':
            accounts.update(conta_suspensa=False)
            AdminAuditLog.objects.create(
                user=request.user,
                action=f'Reactivated {len(user_ids)} accounts',
                ip_address=self.get_client_ip(request)
            )
            messages.success(request, f'Successfully reactivated {len(user_ids)} accounts.')
        
        return redirect('admin_panel:users_dashboard')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class UserExportView(LoginRequiredMixin, View):
    login_url = 'admin_panel:login'
    
    def get(self, request):
        queryset = User.objects.select_related('account', 'account__account_type').all()
        
        form = UserSearchForm(request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(email__icontains=search) | 
                    Q(account__account_no__icontains=search)
                )
        
        AdminAuditLog.objects.create(
            user=request.user,
            action='Exported user data',
            ip_address=self.get_client_ip(request)
        )
        
        return export_users_csv(queryset)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class TransactionsDashboardView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'admin_panel/transactions_dashboard.html'
    context_object_name = 'transactions'
    paginate_by = 50
    login_url = 'admin_panel:login'
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('account', 'account__user').all()
        
        form = TransactionFilterForm(self.request.GET)
        if form.is_valid():
            date_from = form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(timestamp__date__gte=date_from)
            
            date_to = form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(timestamp__date__lte=date_to)
            
            transaction_type = form.cleaned_data.get('transaction_type')
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            
            amount_min = form.cleaned_data.get('amount_min')
            if amount_min:
                queryset = queryset.filter(amount__gte=amount_min)
            
            amount_max = form.cleaned_data.get('amount_max')
            if amount_max:
                queryset = queryset.filter(amount__lte=amount_max)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = TransactionFilterForm(self.request.GET)
        
        today = timezone.now().date()
        today_transactions = Transaction.objects.filter(timestamp__date=today)
        context['today_total'] = today_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        context['today_count'] = today_transactions.count()
        context['today_avg'] = today_transactions.aggregate(Avg('amount'))['amount__avg'] or 0
        
        return context


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/analytics_dashboard.html'
    login_url = 'admin_panel:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kpis'] = calculate_kpis()
        
        account_types = UserBankAccount.objects.values('account_type__name').annotate(
            count=Count('id')
        )
        context['account_type_data'] = list(account_types)
        
        transaction_types = Transaction.objects.values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        context['transaction_type_data'] = list(transaction_types)
        
        top_accounts = UserBankAccount.objects.select_related('user').order_by('-balance')[:10]
        context['top_accounts'] = top_accounts
        
        last_30_days = timezone.now() - timedelta(days=30)
        daily_users = User.objects.filter(date_joined__gte=last_30_days).extra(
            select={'day': 'date(date_joined)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        context['user_growth_data'] = list(daily_users)
        
        return context


class AnalyticsExportView(LoginRequiredMixin, View):
    login_url = 'admin_panel:login'
    
    def get(self, request):
        export_type = request.GET.get('type', 'pdf')
        
        AdminAuditLog.objects.create(
            user=request.user,
            action=f'Exported analytics report ({export_type})',
            ip_address=self.get_client_ip(request)
        )
        
        if export_type == 'pdf':
            return export_analytics_pdf()
        else:
            return export_transactions_csv(Transaction.objects.all())
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class FraudDashboardView(LoginRequiredMixin, ListView):
    model = FraudAlert
    template_name = 'admin_panel/fraud_dashboard.html'
    context_object_name = 'alerts'
    paginate_by = 25
    login_url = 'admin_panel:login'
    
    def get_queryset(self):
        return FraudAlert.objects.select_related('account', 'rule', 'investigated_by').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = FraudAlert.objects.filter(status='PENDING').count()
        context['critical_count'] = FraudAlert.objects.filter(severity='CRITICAL').count()
        context['rules'] = FraudRule.objects.filter(is_active=True)
        return context


class FraudAlertDetailView(LoginRequiredMixin, View):
    login_url = 'admin_panel:login'
    
    def get(self, request, pk):
        alert = get_object_or_404(FraudAlert, pk=pk)
        form = FraudAlertForm(instance=alert)
        return render(request, 'admin_panel/fraud_alert_detail.html', {
            'alert': alert,
            'form': form
        })
    
    def post(self, request, pk):
        alert = get_object_or_404(FraudAlert, pk=pk)
        form = FraudAlertForm(request.POST, instance=alert)
        
        if form.is_valid():
            alert = form.save(commit=False)
            alert.investigated_by = request.user
            if alert.status == 'RESOLVED':
                alert.resolved_at = timezone.now()
            alert.save()
            
            AdminAuditLog.objects.create(
                user=request.user,
                action=f'Updated fraud alert #{alert.id}',
                target_model='FraudAlert',
                target_id=alert.id,
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(request, 'Fraud alert updated successfully.')
            return redirect('admin_panel:fraud_dashboard')
        
        return render(request, 'admin_panel/fraud_alert_detail.html', {
            'alert': alert,
            'form': form
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class HealthDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_panel/health_dashboard.html'
    login_url = 'admin_panel:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['health_data'] = get_system_health()
        context['recent_errors'] = AdminAuditLog.objects.filter(
            action__icontains='error'
        ).order_by('-timestamp')[:10]
        
        try:
            from celery.task.control import inspect
            i = inspect()
            stats = i.stats()
            context['celery_workers'] = len(stats) if stats else 0
        except:
            context['celery_workers'] = 0
        
        return context
