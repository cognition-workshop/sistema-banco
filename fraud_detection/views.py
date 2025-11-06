from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .models import FraudRule, FraudAlert
from .forms import FraudRuleForm, FraudAlertFilterForm


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class FraudRuleListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = FraudRule
    template_name = 'fraud_detection/rule_list.html'
    context_object_name = 'rules'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.GET.get('is_active')
        severity = self.request.GET.get('severity')

        if is_active:
            queryset = queryset.filter(is_active=(is_active == 'true'))
        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset


class FraudRuleCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = FraudRule
    form_class = FraudRuleForm
    template_name = 'fraud_detection/rule_form.html'
    success_url = reverse_lazy('fraud_detection:rule_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fraud rule created successfully')
        return super().form_valid(form)


class FraudRuleUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = FraudRule
    form_class = FraudRuleForm
    template_name = 'fraud_detection/rule_form.html'
    success_url = reverse_lazy('fraud_detection:rule_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fraud rule updated successfully')
        return super().form_valid(form)


class FraudRuleDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = FraudRule
    template_name = 'fraud_detection/rule_confirm_delete.html'
    success_url = reverse_lazy('fraud_detection:rule_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Fraud rule deleted successfully')
        return super().delete(request, *args, **kwargs)


class FraudAlertListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = FraudAlert
    template_name = 'fraud_detection/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'transaction', 'rule', 'account', 'resolved_by'
        )
        
        status = self.request.GET.get('status')
        severity = self.request.GET.get('severity')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FraudAlertFilterForm(self.request.GET or None)
        return context


class FraudAlertDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = FraudAlert
    template_name = 'fraud_detection/alert_detail.html'
    context_object_name = 'alert'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'transaction', 'rule', 'account', 'account__user', 'resolved_by'
        )


class FraudAlertResolveView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, pk):
        alert = get_object_or_404(FraudAlert, pk=pk)
        
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.notes = request.POST.get('notes', '')
        alert.save()

        messages.success(request, f'Alert #{alert.id} has been resolved')
        return redirect('fraud_detection:alert_list')
