from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.http import FileResponse
from django.core.files import File

from .models import IRPFReport
from .utils import generate_irpf_data, generate_irpf_pdf, generate_irpf_csv


class IRPFReportListView(ListView):
    model = IRPFReport
    template_name = 'reports/irpf_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        if demo_user and hasattr(demo_user, 'account'):
            return IRPFReport.objects.filter(account=demo_user.account)
        return IRPFReport.objects.none()


def generate_irpf_report_view(request):
    """Generate IRPF report for a specific year."""
    User = get_user_model()
    demo_user = User.objects.filter(email='demo@example.com').first()
    account = demo_user.account if demo_user and hasattr(demo_user, 'account') else None
    
    if not account:
        messages.error(request, 'Conta não encontrada.')
        return redirect('home')
    
    if request.method == 'POST':
        year = int(request.POST.get('year'))
        
        report, created = IRPFReport.objects.get_or_create(
            account=account,
            year=year
        )
        
        data = generate_irpf_data(account, year)
        report.total_interest_earned = data['total_interest']
        
        pdf_buffer = generate_irpf_pdf(data)
        report.report_file.save(
            f'irpf_{year}_{account.user.cpf}.pdf',
            File(pdf_buffer),
            save=False
        )
        
        csv_buffer = generate_irpf_csv(data)
        report.csv_file.save(
            f'irpf_{year}_{account.user.cpf}.csv',
            File(csv_buffer.getvalue().encode(), name='temp.csv'),
            save=False
        )
        
        report.save()
        
        messages.success(request, f'Relatório IRPF {year} gerado com sucesso!')
        return redirect('reports:irpf_list')
    
    from django.utils import timezone
    current_year = timezone.now().year
    years = range(current_year, current_year - 10, -1)
    
    return render(request, 'reports/generate_irpf.html', {'years': years})


def download_irpf_pdf_view(request, report_id):
    """Download IRPF PDF report."""
    report = get_object_or_404(IRPFReport, id=report_id)
    return FileResponse(report.report_file.open(), as_attachment=True, filename=f'irpf_{report.year}.pdf')


def download_irpf_csv_view(request, report_id):
    """Download IRPF CSV report."""
    report = get_object_or_404(IRPFReport, id=report_id)
    return FileResponse(report.csv_file.open(), as_attachment=True, filename=f'irpf_{report.year}.csv')
