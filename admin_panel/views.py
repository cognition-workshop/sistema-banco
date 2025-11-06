from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from accounts.models import User, UserBankAccount
from transactions.models import Transaction
from .models import AdminPermissionGroup, UserSuspension
import logging

logger = logging.getLogger(__name__)


def is_admin_or_manager(user):
    if not user.is_authenticated:
        return False
    try:
        return user.admin_permission.can_manage_users()
    except AdminPermissionGroup.DoesNotExist:
        return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def user_list_view(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    users = User.objects.select_related('account', 'account__account_type').all()
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(account__account_no__icontains=search_query)
        )
    
    if status_filter == 'suspended':
        suspended_accounts = UserSuspension.objects.filter(
            is_active=True
        ).values_list('account_id', flat=True)
        users = users.filter(account__id__in=suspended_accounts)
    elif status_filter == 'active':
        suspended_accounts = UserSuspension.objects.filter(
            is_active=True
        ).values_list('account_id', flat=True)
        users = users.exclude(account__id__in=suspended_accounts)
    
    users = users.order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    suspended_accounts_ids = set(UserSuspension.objects.filter(
        is_active=True
    ).values_list('account_id', flat=True))
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'suspended_accounts_ids': suspended_accounts_ids,
        'total_users': users.count(),
    }
    
    logger.info(f'Admin {request.user.email} accessed user list')
    return render(request, 'admin_panel/user_list.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    account = user.account
    
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:10]
    
    transaction_stats = Transaction.objects.filter(account=account).aggregate(
        total_deposits=Sum('amount', filter=Q(transaction_type='DEPOSIT')),
        total_withdrawals=Sum('amount', filter=Q(transaction_type='WITHDRAWAL')),
        total_interest=Sum('amount', filter=Q(transaction_type='INTEREST')),
        total_count=Count('id')
    )
    
    suspensions = UserSuspension.objects.filter(account=account).order_by('-suspended_at')
    is_suspended = suspensions.filter(is_active=True).exists()
    
    context = {
        'user': user,
        'account': account,
        'transactions': transactions,
        'transaction_stats': transaction_stats,
        'suspensions': suspensions,
        'is_suspended': is_suspended,
    }
    
    logger.info(f'Admin {request.user.email} viewed user {user.email} details')
    return render(request, 'admin_panel/user_detail.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def suspend_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    account = user.account
    
    existing_suspension = UserSuspension.objects.filter(
        account=account,
        is_active=True
    ).first()
    
    if existing_suspension:
        messages.warning(request, f'A conta {account.account_no} já está suspensa.')
        return redirect('admin_panel:user_detail', user_id=user_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, 'Por favor, forneça um motivo para a suspensão.')
            return redirect('admin_panel:user_detail', user_id=user_id)
        
        UserSuspension.objects.create(
            account=account,
            suspended_by=request.user,
            reason=reason,
            is_active=True
        )
        
        messages.success(request, f'Conta {account.account_no} suspensa com sucesso.')
        logger.warning(f'Admin {request.user.email} suspended account {account.account_no}')
        
        return redirect('admin_panel:user_detail', user_id=user_id)
    
    return render(request, 'admin_panel/suspend_user.html', {'user': user, 'account': account})


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def unsuspend_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    account = user.account
    
    suspension = UserSuspension.objects.filter(
        account=account,
        is_active=True
    ).first()
    
    if not suspension:
        messages.warning(request, f'A conta {account.account_no} não está suspensa.')
        return redirect('admin_panel:user_detail', user_id=user_id)
    
    suspension.is_active = False
    suspension.unsuspended_at = timezone.now()
    suspension.unsuspended_by = request.user
    suspension.save()
    
    messages.success(request, f'Conta {account.account_no} reativada com sucesso.')
    logger.info(f'Admin {request.user.email} unsuspended account {account.account_no}')
    
    return redirect('admin_panel:user_detail', user_id=user_id)


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_accounts = UserBankAccount.objects.count()
    suspended_count = UserSuspension.objects.filter(is_active=True).count()
    
    total_balance = UserBankAccount.objects.aggregate(
        total=Sum('balance')
    )['total'] or 0
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_suspensions = UserSuspension.objects.filter(
        is_active=True
    ).order_by('-suspended_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_accounts': total_accounts,
        'suspended_count': suspended_count,
        'total_balance': total_balance,
        'recent_users': recent_users,
        'recent_suspensions': recent_suspensions,
    }
    
    logger.info(f'Admin {request.user.email} accessed admin dashboard')
    return render(request, 'admin_panel/admin_dashboard.html', context)
