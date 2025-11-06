from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
import csv
import psutil

from transactions.models import Transaction
from transactions.constants import TRANSACTION_TYPE_CHOICES, DEPOSIT, WITHDRAWAL, INTEREST
from accounts.models import User, UserBankAccount, UserAddress
from .models import FraudAlert, SystemHealthLog
from .forms import (
    UserSearchForm, UserEditForm, TransactionFilterForm,
    FraudAlertReviewForm, DateRangeForm
)

User = get_user_model()


class AdminDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    permission_required = 'accounts.view_all_users'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['total_accounts'] = UserBankAccount.objects.count()
        context['total_transactions'] = Transaction.objects.count()
        
        context['recent_transactions'] = Transaction.objects.select_related(
            'account__user'
        ).order_by('-timestamp')[:10]
        
        context['pending_alerts'] = FraudAlert.objects.filter(
            status='pending'
        ).count()
        
        return context


class UserManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'admin_panel/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    permission_required = 'accounts.view_all_users'
    
    def get_queryset(self):
        queryset = User.objects.select_related('account', 'address').all()
        form = UserSearchForm(self.request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            
            if search:
                queryset = queryset.filter(
                    Q(email__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            
            if status:
                if status == 'active':
                    queryset = queryset.filter(is_active=True)
                elif status == 'inactive':
                    queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserSearchForm(self.request.GET)
        return context


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = User
    template_name = 'admin_panel/user_detail.html'
    context_object_name = 'user_obj'
    permission_required = 'accounts.view_all_users'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        if hasattr(user_obj, 'account'):
            context['transactions'] = Transaction.objects.filter(
                account=user_obj.account
            ).order_by('-timestamp')[:20]
        else:
            context['transactions'] = []
        
        return context


class UserEditView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'admin_panel/user_edit.html'
    permission_required = 'accounts.edit_user_details'
    success_url = reverse_lazy('admin_panel:user_management')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.get_object()
        return context


@login_required
@permission_required('accounts.suspend_user', raise_exception=True)
def toggle_user_status(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    return redirect('admin_panel:user_detail', pk=pk)


class TransactionMonitoringView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Transaction
    template_name = 'admin_panel/transaction_monitoring.html'
    context_object_name = 'transactions'
    paginate_by = 50
    permission_required = 'accounts.view_all_transactions'
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'account__user'
        ).all()
        
        form = TransactionFilterForm(self.request.GET)
        if form.is_valid():
            user_email = form.cleaned_data.get('user_email')
            transaction_type = form.cleaned_data.get('transaction_type')
            min_amount = form.cleaned_data.get('min_amount')
            max_amount = form.cleaned_data.get('max_amount')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if user_email:
                queryset = queryset.filter(account__user__email__icontains=user_email)
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            if min_amount:
                queryset = queryset.filter(amount__gte=min_amount)
            if max_amount:
                queryset = queryset.filter(amount__lte=max_amount)
            if date_from:
                queryset = queryset.filter(timestamp__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = TransactionFilterForm(self.request.GET)
        
        queryset = self.get_queryset()
        context['total_volume'] = queryset.aggregate(total=Sum('amount'))['total'] or 0
        context['avg_transaction'] = queryset.aggregate(avg=Avg('amount'))['avg'] or 0
        
        return context


class AnalyticsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admin_panel/analytics.html'
    permission_required = 'accounts.view_all_transactions'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = DateRangeForm(self.request.GET)
        if form.is_valid() and form.cleaned_data.get('date_from'):
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data.get('date_to') or timezone.now().date()
        else:
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=30)
        
        context['date_form'] = DateRangeForm(initial={'date_from': date_from, 'date_to': date_to})
        
        transactions = Transaction.objects.filter(
            timestamp__date__gte=date_from,
            timestamp__date__lte=date_to
        )
        
        context['total_transactions'] = transactions.count()
        context['total_volume'] = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        by_type = {}
        for type_id, type_name in TRANSACTION_TYPE_CHOICES:
            count = transactions.filter(transaction_type=type_id).count()
            by_type[type_name] = count
        context['transactions_by_type'] = json.dumps(by_type)
        
        from django.db.models.functions import TruncDate
        daily_stats = transactions.annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            count=Count('id'),
            volume=Sum('amount')
        ).order_by('date')
        
        dates = [str(item['date']) for item in daily_stats]
        volumes = [float(item['volume']) for item in daily_stats]
        counts = [item['count'] for item in daily_stats]
        
        context['chart_dates'] = json.dumps(dates)
        context['chart_volumes'] = json.dumps(volumes)
        context['chart_counts'] = json.dumps(counts)
        
        return context


@login_required
@permission_required('accounts.export_data', raise_exception=True)
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'User Email', 'Account Number', 'Type', 'Amount', 'Balance After', 'Timestamp'])
    
    transactions = Transaction.objects.select_related('account__user').all()
    
    form = TransactionFilterForm(request.GET)
    if form.is_valid():
        user_email = form.cleaned_data.get('user_email')
        transaction_type = form.cleaned_data.get('transaction_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if user_email:
            transactions = transactions.filter(account__user__email__icontains=user_email)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if date_from:
            transactions = transactions.filter(timestamp__date__gte=date_from)
        if date_to:
            transactions = transactions.filter(timestamp__date__lte=date_to)
    
    for transaction in transactions.order_by('-timestamp'):
        writer.writerow([
            transaction.id,
            transaction.account.user.email,
            transaction.account.account_no,
            transaction.get_transaction_type_display(),
            transaction.amount,
            transaction.balance_after_transaction,
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@login_required
@permission_required('accounts.export_data', raise_exception=True)
def export_transactions_excel(request):
    import openpyxl
    from openpyxl.styles import Font
    from io import BytesIO
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"
    
    headers = ['Transaction ID', 'User Email', 'Account Number', 'Type', 'Amount', 'Balance After', 'Timestamp']
    ws.append(headers)
    
    for cell in ws[1]:
        cell.font = Font(bold=True)
    
    transactions = Transaction.objects.select_related('account__user').all()
    
    form = TransactionFilterForm(request.GET)
    if form.is_valid():
        user_email = form.cleaned_data.get('user_email')
        transaction_type = form.cleaned_data.get('transaction_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if user_email:
            transactions = transactions.filter(account__user__email__icontains=user_email)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if date_from:
            transactions = transactions.filter(timestamp__date__gte=date_from)
        if date_to:
            transactions = transactions.filter(timestamp__date__lte=date_to)
    
    for transaction in transactions.order_by('-timestamp'):
        ws.append([
            transaction.id,
            transaction.account.user.email,
            transaction.account.account_no,
            transaction.get_transaction_type_display(),
            float(transaction.amount),
            float(transaction.balance_after_transaction),
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
    
    return response


class FraudDetectionView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FraudAlert
    template_name = 'admin_panel/fraud_detection.html'
    context_object_name = 'alerts'
    paginate_by = 20
    permission_required = 'accounts.view_fraud_alerts'
    
    def get_queryset(self):
        queryset = FraudAlert.objects.select_related(
            'transaction__account__user',
            'reviewed_by'
        ).all()
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_count'] = FraudAlert.objects.filter(status='pending').count()
        context['statuses'] = FraudAlert.STATUS_CHOICES
        return context


class FraudAlertDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = FraudAlert
    template_name = 'admin_panel/fraud_alert_detail.html'
    context_object_name = 'alert'
    permission_required = 'accounts.view_fraud_alerts'


@login_required
@permission_required('accounts.review_fraud_alerts', raise_exception=True)
def review_fraud_alert(request, pk):
    alert = get_object_or_404(FraudAlert, pk=pk)
    
    if request.method == 'POST':
        form = FraudAlertReviewForm(request.POST, instance=alert)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.reviewed_by = request.user
            alert.reviewed_at = timezone.now()
            alert.save()
            return redirect('admin_panel:fraud_detection')
    else:
        form = FraudAlertReviewForm(instance=alert)
    
    return render(request, 'admin_panel/fraud_alert_review.html', {
        'form': form,
        'alert': alert
    })


class SystemHealthView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admin_panel/system_health.html'
    permission_required = 'accounts.view_system_health'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from celery import current_app
        try:
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            context['celery_status'] = 'healthy' if active_workers else 'down'
            context['active_workers'] = len(active_workers) if active_workers else 0
        except Exception as e:
            context['celery_status'] = 'error'
            context['celery_error'] = str(e)
            context['active_workers'] = 0
        
        from django.core.cache import cache
        try:
            cache.set('health_check', 'ok', 1)
            redis_status = cache.get('health_check') == 'ok'
            context['redis_status'] = 'healthy' if redis_status else 'down'
        except Exception as e:
            context['redis_status'] = 'error'
            context['redis_error'] = str(e)
        
        context['cpu_usage'] = psutil.cpu_percent(interval=1)
        context['memory_usage'] = psutil.virtual_memory().percent
        context['disk_usage'] = psutil.disk_usage('/').percent
        
        context['total_users'] = User.objects.count()
        context['total_transactions'] = Transaction.objects.count()
        context['recent_transactions'] = Transaction.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        context['health_logs'] = SystemHealthLog.objects.all()[:10]
        
        return context


@login_required
@permission_required('accounts.view_system_health', raise_exception=True)
def log_system_health(request):
    from celery import current_app
    import redis
    
    inspect = current_app.control.inspect()
    active_workers = inspect.active()
    workers_count = len(active_workers) if active_workers else 0
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_connected = redis_client.ping()
    redis_info = redis_client.info('memory')
    redis_memory = redis_info.get('used_memory_human', 'Unknown')
    
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    
    import os
    from django.conf import settings
    db_path = settings.DATABASES['default']['NAME']
    db_size = os.path.getsize(db_path) / (1024 * 1024)
    
    SystemHealthLog.objects.create(
        celery_workers_active=workers_count,
        redis_connected=redis_connected,
        redis_memory_usage=redis_memory,
        database_size=f"{db_size:.2f} MB",
        cpu_usage=cpu,
        memory_usage=memory
    )
    
    return JsonResponse({'status': 'success', 'message': 'Health log created'})
