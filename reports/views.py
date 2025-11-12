import csv
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import ListView
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from transactions.constants import INTEREST
from transactions.models import Transaction
from .forms import IRPFYearFilterForm


class IRPFReportView(ListView):
    template_name = 'reports/irpf_report.html'
    model = Transaction
    context_object_name = 'monthly_data'
    
    def get(self, request, *args, **kwargs):
        self.form = IRPFYearFilterForm(request.GET or None)
        self.selected_year = None
        
        if self.form.is_valid() and self.form.cleaned_data.get('year'):
            self.selected_year = int(self.form.cleaned_data['year'])
        else:
            self.selected_year = timezone.now().year
            
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            return Transaction.objects.none()
        
        queryset = Transaction.objects.filter(
            account=demo_user.account,
            transaction_type=INTEREST,
            timestamp__year=self.selected_year
        )
        
        monthly_data = queryset.annotate(
            month=TruncMonth('timestamp')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        return monthly_data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        annual_total = sum(item['total'] for item in context['monthly_data'])
        
        context.update({
            'form': self.form,
            'selected_year': self.selected_year,
            'annual_total': annual_total,
            'account': demo_user.account if demo_user and hasattr(demo_user, 'account') else None,
        })
        
        return context


class IRPFExportCSVView(ListView):
    model = Transaction
    
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        if not year:
            year = timezone.now().year
        else:
            year = int(year)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            return HttpResponse('No account found', status=404)
        
        queryset = Transaction.objects.filter(
            account=demo_user.account,
            transaction_type=INTEREST,
            timestamp__year=year
        ).annotate(
            month=TruncMonth('timestamp')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="irpf_report_{year}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Mês', 'Juros Recebidos (R$)'])
        
        for item in queryset:
            month_name = item['month'].strftime('%B %Y')
            writer.writerow([month_name, f'{item["total"]:.2f}'])
        
        annual_total = sum(item['total'] for item in queryset)
        writer.writerow(['Total Anual', f'{annual_total:.2f}'])
        
        return response


class IRPFExportPDFView(ListView):
    model = Transaction
    
    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        if not year:
            year = timezone.now().year
        else:
            year = int(year)
        
        User = get_user_model()
        demo_user = User.objects.filter(email='demo@example.com').first()
        
        if not demo_user or not hasattr(demo_user, 'account'):
            return HttpResponse('No account found', status=404)
        
        account = demo_user.account
        
        queryset = Transaction.objects.filter(
            account=account,
            transaction_type=INTEREST,
            timestamp__year=year
        ).annotate(
            month=TruncMonth('timestamp')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        title = Paragraph(f'<b>Relatório de Rendimentos IRPF - {year}</b>', styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        account_info = Paragraph(
            f'<b>Titular:</b> {demo_user.get_full_name() or demo_user.email}<br/>'
            f'<b>Conta:</b> {account.account_no}<br/>'
            f'<b>Data de Geração:</b> {timezone.now().strftime("%d/%m/%Y")}',
            styles['Normal']
        )
        elements.append(account_info)
        elements.append(Spacer(1, 0.3*inch))
        
        data = [['Mês', 'Juros Recebidos (R$)']]
        for item in queryset:
            month_name = item['month'].strftime('%B %Y')
            data.append([month_name, f'R$ {item["total"]:.2f}'])
        
        annual_total = sum(item['total'] for item in queryset)
        data.append(['Total Anual', f'R$ {annual_total:.2f}'])
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="irpf_report_{year}.pdf"'
        response.write(pdf)
        
        return response
