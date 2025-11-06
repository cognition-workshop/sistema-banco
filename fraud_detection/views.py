from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import FraudAlert


@method_decorator(staff_member_required, name='dispatch')
class FraudAlertListView(ListView):
    model = FraudAlert
    template_name = 'admin/fraud_alerts.html'
    context_object_name = 'alerts'
    paginate_by = 50
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('user')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


@staff_member_required
def mark_alert_reviewed(request, alert_id):
    alert = get_object_or_404(FraudAlert, id=alert_id)
    alert.status = 'REVIEWED'
    alert.reviewed_at = timezone.now()
    alert.save()
    messages.success(request, 'Alert marked as reviewed')
    return redirect('fraud_detection:alerts')
