from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from transactions.models import Transaction, FraudAlert
from transactions.constants import DEPOSIT, WITHDRAWAL, INTEREST
from accounts.models import UserBankAccount, User


@staff_member_required
def transaction_dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_transactions = Transaction.objects.count()
    today_transactions = Transaction.objects.filter(timestamp__date=today).count()
    week_transactions = Transaction.objects.filter(timestamp__date__gte=week_ago).count()
    
    transactions_by_type = Transaction.objects.values('transaction_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    large_transactions = Transaction.objects.filter(
        amount__gte=Decimal('5000.00')
    ).select_related('account', 'account__user').order_by('-timestamp')[:10]
    
    deposits = Transaction.objects.filter(transaction_type=DEPOSIT)
    withdrawals = Transaction.objects.filter(transaction_type=WITHDRAWAL)
    
    deposit_stats = deposits.aggregate(
        count=Count('id'),
        total=Sum('amount'),
        avg=Avg('amount')
    )
    
    withdrawal_stats = withdrawals.aggregate(
        count=Count('id'),
        total=Sum('amount'),
        avg=Avg('amount')
    )
    
    daily_transactions = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = Transaction.objects.filter(timestamp__date=date).count()
        daily_transactions.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_transactions.reverse()
    
    context = {
        'title': 'Dashboard de Transações',
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'week_transactions': week_transactions,
        'transactions_by_type': transactions_by_type,
        'large_transactions': large_transactions,
        'deposit_stats': deposit_stats,
        'withdrawal_stats': withdrawal_stats,
        'daily_transactions': daily_transactions,
    }
    
    return render(request, 'admin/transaction_dashboard.html', context)


@staff_member_required
def analytics_dashboard(request):
    total_accounts = UserBankAccount.objects.count()
    active_accounts = UserBankAccount.objects.filter(balance__gt=0).count()
    total_balance = UserBankAccount.objects.aggregate(total=Sum('balance'))['total'] or 0
    avg_balance = UserBankAccount.objects.aggregate(avg=Avg('balance'))['avg'] or 0
    
    top_accounts = UserBankAccount.objects.select_related('user').order_by('-balance')[:10]
    
    week_ago = timezone.now() - timedelta(days=7)
    hourly_data = [0] * 24
    transactions = Transaction.objects.filter(timestamp__gte=week_ago)
    for trans in transactions:
        hourly_data[trans.timestamp.hour] += 1
    
    account_type_dist = UserBankAccount.objects.values('account_type__name').annotate(
        count=Count('id'),
        total_balance=Sum('balance')
    )
    
    context = {
        'title': 'Analytics e Relatórios',
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'total_balance': total_balance,
        'avg_balance': avg_balance,
        'top_accounts': top_accounts,
        'hourly_data': hourly_data,
        'account_type_dist': account_type_dist,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required
def system_health_dashboard(request):
    import redis
    from django.db import connection
    
    health_status = {
        'database': {'status': 'unknown', 'message': ''},
        'redis': {'status': 'unknown', 'message': ''},
        'celery': {'status': 'unknown', 'message': ''},
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['database'] = {'status': 'healthy', 'message': 'Conexão OK'}
    except Exception as e:
        health_status['database'] = {'status': 'error', 'message': str(e)}
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        info = r.info()
        health_status['redis'] = {
            'status': 'healthy',
            'message': f'Conectado - {info.get("connected_clients", 0)} clientes',
            'memory': info.get('used_memory_human', 'N/A'),
            'uptime': info.get('uptime_in_days', 0)
        }
    except Exception as e:
        health_status['redis'] = {'status': 'error', 'message': str(e)}
    
    try:
        from banking_system.celery import app
        inspect = app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        if stats:
            worker_count = len(stats)
            active_tasks = sum(len(tasks) for tasks in (active or {}).values())
            health_status['celery'] = {
                'status': 'healthy',
                'message': f'{worker_count} worker(s) ativo(s), {active_tasks} tarefa(s) em execução'
            }
        else:
            health_status['celery'] = {'status': 'warning', 'message': 'Nenhum worker ativo'}
    except Exception as e:
        health_status['celery'] = {'status': 'error', 'message': str(e)}
    
    recent_transactions = Transaction.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    pending_alerts = FraudAlert.objects.filter(status='PENDING').count()
    
    context = {
        'title': 'Saúde do Sistema',
        'health_status': health_status,
        'recent_transactions': recent_transactions,
        'pending_alerts': pending_alerts,
    }
    
    return render(request, 'admin/system_health_dashboard.html', context)
