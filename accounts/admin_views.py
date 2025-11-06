from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, UserBankAccount, BankAccountType
from transactions.models import Transaction
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST


@staff_member_required
def analytics_dashboard(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_this_month = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    total_accounts = UserBankAccount.objects.count()
    total_balance = UserBankAccount.objects.aggregate(total=Sum('balance'))['total'] or 0
    avg_balance = UserBankAccount.objects.aggregate(avg=Avg('balance'))['avg'] or 0
    
    total_transactions = Transaction.objects.count()
    transactions_this_month = Transaction.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    total_deposits = Transaction.objects.filter(
        transaction_type=DEPOSIT
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type=WITHDRAWAL
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_interest = Transaction.objects.filter(
        transaction_type=INTEREST
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    account_type_stats = BankAccountType.objects.annotate(
        count=Count('accounts'),
        total_balance=Sum('accounts__balance')
    ).values('name', 'count', 'total_balance')
    
    recent_transactions = Transaction.objects.select_related(
        'account__user', 'account__account_type'
    ).order_by('-timestamp')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'total_accounts': total_accounts,
        'total_balance': total_balance,
        'avg_balance': avg_balance,
        'total_transactions': total_transactions,
        'transactions_this_month': transactions_this_month,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_interest': total_interest,
        'account_type_stats': account_type_stats,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required
def fraud_detection_dashboard(request):
    suspicious_transactions = []
    
    for transaction in Transaction.objects.filter(
        transaction_type=WITHDRAWAL
    ).select_related('account__account_type', 'account__user'):
        if transaction.amount > transaction.account.account_type.maximum_withdrawal_amount:
            suspicious_transactions.append({
                'transaction': transaction,
                'reason': f'Exceeds withdrawal limit (${transaction.account.account_type.maximum_withdrawal_amount:.2f})',
                'severity': 'high'
            })
    
    large_transactions = Transaction.objects.filter(
        amount__gt=50000
    ).select_related('account__user', 'account__account_type')
    
    for transaction in large_transactions:
        suspicious_transactions.append({
            'transaction': transaction,
            'reason': f'Large amount (${transaction.amount:.2f})',
            'severity': 'medium'
        })
    
    one_hour_ago = timezone.now() - timedelta(hours=1)
    accounts_with_multiple = Transaction.objects.filter(
        timestamp__gte=one_hour_ago
    ).values('account').annotate(
        count=Count('id')
    ).filter(count__gte=5)
    
    for item in accounts_with_multiple:
        transactions = Transaction.objects.filter(
            account_id=item['account'],
            timestamp__gte=one_hour_ago
        ).select_related('account__user')
        
        if transactions.exists():
            suspicious_transactions.append({
                'transaction': transactions.first(),
                'reason': f'Multiple transactions ({item["count"]}) in last hour',
                'severity': 'high'
            })
    
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    suspicious_transactions.sort(key=lambda x: severity_order[x['severity']])
    
    context = {
        'suspicious_transactions': suspicious_transactions,
        'total_suspicious': len(suspicious_transactions),
    }
    
    return render(request, 'admin/fraud_detection_dashboard.html', context)


@staff_member_required
def system_health_dashboard(request):
    transactions_last_hour = Transaction.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    transactions_last_24h = Transaction.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    active_users_today = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    accounts_with_zero_balance = UserBankAccount.objects.filter(balance=0).count()
    accounts_with_negative_balance = UserBankAccount.objects.filter(balance__lt=0).count()
    
    total_records = (
        User.objects.count() +
        UserBankAccount.objects.count() +
        Transaction.objects.count()
    )
    
    health_score = 100
    
    if accounts_with_negative_balance > 0:
        health_score -= 10
    
    if transactions_last_hour == 0:
        health_score -= 20
    
    if active_users_today == 0:
        health_score -= 30
    
    health_status = 'Excellent' if health_score >= 90 else 'Good' if health_score >= 70 else 'Fair' if health_score >= 50 else 'Poor'
    health_color = 'green' if health_score >= 90 else 'orange' if health_score >= 70 else 'yellow' if health_score >= 50 else 'red'
    
    context = {
        'health_score': health_score,
        'health_status': health_status,
        'health_color': health_color,
        'transactions_last_hour': transactions_last_hour,
        'transactions_last_24h': transactions_last_24h,
        'active_users_today': active_users_today,
        'accounts_with_zero_balance': accounts_with_zero_balance,
        'accounts_with_negative_balance': accounts_with_negative_balance,
        'total_records': total_records,
    }
    
    return render(request, 'admin/system_health_dashboard.html', context)
