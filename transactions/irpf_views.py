import csv
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView, View
from .irpf_services import IRPFCalculator
from .irpf_models import IRPFReport

User = get_user_model()


class IRPFReportView(TemplateView):
    template_name = 'transactions/irpf/report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user:
            reports = IRPFReport.objects.filter(user=demo_user).order_by('-year')
            context['reports'] = reports
            context['user'] = demo_user
        
        return context


class IRPFGenerateView(View):
    def post(self, request):
        year = int(request.POST.get('year', 2024))
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if demo_user:
            report = IRPFCalculator.calculate_annual_report(demo_user, year)
            return HttpResponse(f'Relatório IRPF gerado para o ano {year}. <a href="/transactions/irpf/">Ver relatórios</a>')
        
        return HttpResponse('Usuário não encontrado', status=404)


class IRPFExportView(View):
    def get(self, request, report_id, format='pdf'):
        try:
            report = IRPFReport.objects.get(id=report_id)
            
            if format == 'pdf':
                pdf_buffer = IRPFCalculator.generate_irpf_pdf(report)
                response = HttpResponse(pdf_buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="IRPF_{report.year}_{report.user.email}.pdf"'
                return response
            
            elif format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="IRPF_{report.year}_{report.user.email}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Descrição', 'Valor'])
                writer.writerow(['Ano', report.year])
                writer.writerow(['Saldo Inicial', f'{report.opening_balance}'])
                writer.writerow(['Total Depósitos', f'{report.total_deposits}'])
                writer.writerow(['Total Saques', f'{report.total_withdrawals}'])
                writer.writerow(['Rendimentos', f'{report.total_interest}'])
                writer.writerow(['Saldo Final', f'{report.closing_balance}'])
                writer.writerow(['Transações', report.transaction_count])
                
                return response
        
        except IRPFReport.DoesNotExist:
            return HttpResponse('Relatório não encontrado', status=404)
