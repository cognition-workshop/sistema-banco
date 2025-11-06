from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import FraudAlert


class FraudAlertListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'fraud_detection/alert_list.html'
    model = FraudAlert
    permission_required = 'transactions.view_transaction'
    context_object_name = 'alerts'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = FraudAlert.objects.select_related('account__user').all()
        
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.filter(status='pending')
        
        return queryset.order_by('-created_at')


class FraudAlertDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = 'fraud_detection/alert_detail.html'
    model = FraudAlert
    permission_required = 'transactions.view_transaction'
    context_object_name = 'alert'


def mark_alert_resolved(request, pk):
    if not request.user.has_perm('transactions.change_transaction'):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('fraud_detection:alert_list')
    
    alert = get_object_or_404(FraudAlert, pk=pk)
    alert.status = 'resolved'
    alert.resolved_at = timezone.now()
    alert.save()
    
    messages.success(request, 'Alerta marcado como resolvido.')
    return redirect('fraud_detection:alert_detail', pk=pk)


def mark_alert_false_positive(request, pk):
    if not request.user.has_perm('transactions.change_transaction'):
        messages.error(request, 'Você não tem permissão para esta ação.')
        return redirect('fraud_detection:alert_list')
    
    alert = get_object_or_404(FraudAlert, pk=pk)
    alert.status = 'false_positive'
    alert.resolved_at = timezone.now()
    alert.save()
    
    messages.success(request, 'Alerta marcado como falso positivo.')
    return redirect('fraud_detection:alert_detail', pk=pk)
