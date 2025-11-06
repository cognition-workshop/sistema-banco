from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from .models import FraudAlert
from admin_panel.views import is_admin_or_manager
import logging

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def fraud_dashboard_view(request):
    status_filter = request.GET.get('status', 'all')
    severity_filter = request.GET.get('severity', 'all')
    
    alerts = FraudAlert.objects.select_related('account', 'transaction', 'resolved_by')
    
    if status_filter != 'all':
        alerts = alerts.filter(status=status_filter)
    
    if severity_filter != 'all':
        alerts = alerts.filter(severity=severity_filter)
    
    alerts = alerts.order_by('-created_at')
    
    stats = {
        'total_alerts': FraudAlert.objects.count(),
        'pending_alerts': FraudAlert.objects.filter(status=FraudAlert.STATUS_PENDING).count(),
        'critical_alerts': FraudAlert.objects.filter(severity=FraudAlert.SEVERITY_CRITICAL).count(),
        'resolved_today': FraudAlert.objects.filter(
            status=FraudAlert.STATUS_RESOLVED,
            resolved_at__date=timezone.now().date()
        ).count(),
    }
    
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
        'status_choices': FraudAlert.STATUS_CHOICES,
        'severity_choices': FraudAlert.SEVERITY_CHOICES,
    }
    
    logger.info(f'Admin {request.user.email} accessed fraud detection dashboard')
    return render(request, 'fraud_detection/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='/accounts/login/')
def resolve_alert_view(request, alert_id):
    alert = get_object_or_404(FraudAlert, id=alert_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        resolution_notes = request.POST.get('resolution_notes', '')
        
        if status in [FraudAlert.STATUS_RESOLVED, FraudAlert.STATUS_FALSE_POSITIVE]:
            alert.status = status
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()
            alert.resolution_notes = resolution_notes
            alert.save()
            
            messages.success(request, f'Alerta #{alert.id} resolvido com sucesso.')
            logger.info(f'Admin {request.user.email} resolved fraud alert {alert.id}')
        else:
            messages.error(request, 'Status inválido.')
        
        return redirect('fraud_detection:dashboard')
    
    context = {'alert': alert}
    return render(request, 'fraud_detection/resolve_alert.html', context)
