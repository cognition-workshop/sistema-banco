from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django import forms
from .models import AnnualTaxReport
from .utils import generate_tax_report, generate_pdf_report
import csv
from datetime import datetime


class TaxReportYearForm(forms.Form):
    year = forms.IntegerField(
        min_value=2000,
        max_value=datetime.now().year,
        initial=datetime.now().year - 1,
        label='Ano'
    )


class TaxReportListView(LoginRequiredMixin, ListView):
    model = AnnualTaxReport
    template_name = 'tax_reports/report_list.html'
    context_object_name = 'reports'

    def get_queryset(self):
        return AnnualTaxReport.objects.filter(
            account=self.request.user.account
        )


class TaxReportDetailView(LoginRequiredMixin, DetailView):
    model = AnnualTaxReport
    template_name = 'tax_reports/report_detail.html'
    context_object_name = 'report'

    def get_queryset(self):
        return AnnualTaxReport.objects.filter(
            account=self.request.user.account
        )


class TaxReportGenerateView(LoginRequiredMixin, FormView):
    form_class = TaxReportYearForm
    template_name = 'tax_reports/generate_form.html'
    success_url = reverse_lazy('tax_reports:report_list')

    def form_valid(self, form):
        year = form.cleaned_data['year']
        account = self.request.user.account
        
        report = generate_tax_report(account, year)
        generate_pdf_report(report)
        
        messages.success(
            self.request,
            f'Relatório fiscal de {year} gerado com sucesso!'
        )
        return super().form_valid(form)


def download_pdf_report(request, pk):
    """Download PDF tax report"""
    report = get_object_or_404(
        AnnualTaxReport,
        pk=pk,
        account=request.user.account
    )
    
    if not report.pdf_file:
        generate_pdf_report(report)
    
    return FileResponse(
        report.pdf_file.open('rb'),
        as_attachment=True,
        filename=f'irpf_{report.year}_{report.account.account_no}.pdf'
    )


def export_csv_report(request, pk):
    """Export tax report as CSV"""
    report = get_object_or_404(
        AnnualTaxReport,
        pk=pk,
        account=request.user.account
    )
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="irpf_{report.year}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Descrição', 'Valor (R$)'])
    writer.writerow(['Ano', report.year])
    writer.writerow(['Conta', report.account.account_no])
    writer.writerow(['Saldo Inicial', f'{report.opening_balance:.2f}'])
    writer.writerow(['Total de Depósitos', f'{report.total_deposits:.2f}'])
    writer.writerow(['Total de Saques', f'{report.total_withdrawals:.2f}'])
    writer.writerow(['Juros Recebidos', f'{report.total_interest:.2f}'])
    writer.writerow(['PIX Recebidos', f'{report.total_pix_received:.2f}'])
    writer.writerow(['PIX Enviados', f'{report.total_pix_sent:.2f}'])
    writer.writerow(['Saldo Final', f'{report.closing_balance:.2f}'])
    
    return response
