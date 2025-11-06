import csv
import psutil
import subprocess
from io import BytesIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from accounts.models import User, UserBankAccount
from transactions.models import Transaction

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def export_users_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Account Number', 'Email', 'Name', 'Balance', 'Account Type', 'Status', 'Created Date'])
    
    for user in queryset:
        if hasattr(user, 'account'):
            writer.writerow([
                user.account.account_no,
                user.email,
                f"{user.first_name} {user.last_name}",
                user.account.balance,
                user.account.account_type.name,
                'Suspended' if user.account.conta_suspensa else 'Active',
                user.date_joined.strftime('%Y-%m-%d')
            ])
    
    return response


def export_transactions_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Account Number', 'Type', 'Amount', 'Balance After', 'Date'])
    
    for transaction in queryset:
        writer.writerow([
            transaction.account.account_no,
            transaction.get_transaction_type_display(),
            transaction.amount,
            transaction.balance_after_transaction,
            transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


def export_analytics_pdf():
    if not REPORTLAB_AVAILABLE:
        response = HttpResponse("PDF export is unavailable. Reportlab library is not installed.", content_type='text/plain')
        response.status_code = 500
        return response
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Banking System Analytics Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    total_users = User.objects.count()
    total_accounts = UserBankAccount.objects.count()
    total_transactions = Transaction.objects.count()
    total_balance = UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    data = [
        ['Metric', 'Value'],
        ['Total Users', str(total_users)],
        ['Total Accounts', str(total_accounts)],
        ['Total Transactions', str(total_transactions)],
        ['Total System Balance', f"${total_balance:,.2f}"],
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


def get_system_health():
    health_data = {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'services': {}
    }
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        health_data['services']['redis'] = 'healthy'
    except:
        health_data['services']['redis'] = 'unhealthy'
    
    try:
        from django.db import connection
        connection.ensure_connection()
        health_data['services']['database'] = 'healthy'
    except:
        health_data['services']['database'] = 'unhealthy'
    
    health_data['services']['django'] = 'healthy'
    
    try:
        result = subprocess.run(['celery', '-A', 'banking_system', 'inspect', 'ping'], 
                              capture_output=True, text=True, timeout=5)
        health_data['services']['celery'] = 'healthy' if result.returncode == 0 else 'unhealthy'
    except:
        health_data['services']['celery'] = 'unknown'
    
    total_health = 100
    if health_data['cpu_percent'] > 80:
        total_health -= 20
    if health_data['memory_percent'] > 80:
        total_health -= 20
    if health_data['disk_percent'] > 80:
        total_health -= 20
    for service, status in health_data['services'].items():
        if status != 'healthy':
            total_health -= 10
    
    health_data['health_score'] = max(0, total_health)
    
    return health_data


def calculate_kpis():
    now = timezone.now()
    last_month = now - timedelta(days=30)
    
    total_users = User.objects.count()
    new_users_this_month = User.objects.filter(date_joined__gte=last_month).count()
    
    total_transactions = Transaction.objects.count()
    avg_transaction = Transaction.objects.aggregate(Avg('amount'))['amount__avg'] or 0
    
    active_accounts = UserBankAccount.objects.filter(balance__gt=0).count()
    total_balance = UserBankAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    user_growth_rate = (new_users_this_month / max(total_users - new_users_this_month, 1)) * 100 if total_users > 0 else 0
    
    return {
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,
        'user_growth_rate': round(user_growth_rate, 2),
        'total_transactions': total_transactions,
        'avg_transaction_value': round(avg_transaction, 2),
        'active_accounts': active_accounts,
        'total_system_balance': round(total_balance, 2),
    }


def detect_suspicious_transactions(account):
    alerts = []
    recent_transactions = Transaction.objects.filter(
        account=account,
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-timestamp')
    
    if recent_transactions.count() > 10:
        alerts.append({
            'type': 'HIGH_FREQUENCY',
            'severity': 'MEDIUM',
            'description': f'Account {account.account_no} has made {recent_transactions.count()} transactions in the last 24 hours'
        })
    
    for transaction in recent_transactions[:5]:
        if transaction.amount > 10000:
            alerts.append({
                'type': 'HIGH_VALUE',
                'severity': 'HIGH',
                'description': f'High value transaction of ${transaction.amount} detected on account {account.account_no}'
            })
    
    withdrawals = recent_transactions.filter(transaction_type=2)
    if withdrawals.count() >= 5:
        alerts.append({
            'type': 'SUSPICIOUS_TIMING',
            'severity': 'MEDIUM',
            'description': f'Multiple consecutive withdrawals detected on account {account.account_no}'
        })
    
    return alerts
